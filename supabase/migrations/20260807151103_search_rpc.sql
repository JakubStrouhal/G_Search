-- Migration unit 1: schema_changes
-- Transaction mode: transactional
-- Boundary reason: default

SET check_function_bodies = false;

CREATE EXTENSION unaccent WITH SCHEMA extensions;

CREATE FUNCTION public.fold_query (
  p text
)
  RETURNS text
  LANGUAGE sql
  IMMUTABLE
  PARALLEL SAFE
  SET search_path TO ''
  AS $function$ select lower(trim(extensions.unaccent($1))) $function$;

COMMENT ON FUNCTION public.fold_query(text) IS 'lower + trim + strip diacritics. Used to resolve `masaz tajski` to the logged `masaż tajski`; the caller is always told it happened.';

GRANT ALL ON FUNCTION public.fold_query(text) TO anon;

GRANT ALL ON FUNCTION public.fold_query(text) TO authenticated;

CREATE FUNCTION public.search_deals (
  p_market text,
  p_city   text,
  p_query  text,
  p_limit  integer DEFAULT 12
)
  RETURNS jsonb
  LANGUAGE plpgsql
  SECURITY DEFINER
  SET search_path TO ''
  AS $function$
declare
  cfg              public.search_config;
  q_raw            text := trim(p_query);
  q_exact          text;
  q_emb            extensions.vector(384);
  v_normalised     boolean := false;
  v_max            numeric;
  v_band           text;
  v_class          public.query_classes;
  v_results        jsonb;
  v_matched        jsonb;
  v_available      integer := 0;   -- matches above LOW, BEFORE p_limit
begin
  select * into cfg from public.search_config;

  -- Fail loudly on a missing config. Without this the NULL thresholds make every
  -- comparison NULL, the CASE falls through to its ELSE, and the function abstains
  -- on ABSOLUTELY EVERYTHING while returning 200. A search engine that silently
  -- answers "we have nothing" to every query is the worst possible failure here,
  -- and it would look like a working deploy. Found exactly this way: `db pull`
  -- regenerates schema and not data, so a rebuilt migration dropped the row.
  if cfg.low is null or cfg.high is null then
    raise exception 'search_config is empty or incomplete: thresholds are not loaded. '
                    'Run `python3 supabase/build_seed.py && npx supabase db reset`. '
                    'Refusing to answer rather than silently abstaining on every query.';
  end if;

  if q_raw is null or q_raw = '' then
    return jsonb_build_object('band', 'empty', 'query', p_query);
  end if;

  -- Resolve against the logged set: exact first, then diacritic-folded.
  select qe.q, qe.embedding into q_exact, q_emb
  from public.query_embeddings qe
  where qe.q = lower(q_raw)
  limit 1;

  if q_exact is null then
    select qe.q, qe.embedding into q_exact, q_emb
    from public.query_embeddings qe
    where public.fold_query(qe.q) = public.fold_query(q_raw)
    order by qe.q
    limit 1;
    v_normalised := q_exact is not null;
  end if;

  -- E6: a query the log never saw is REFUSED BY NAME. Returning the nearest
  -- logged query's results would be silent substitution — precisely the failure
  -- this prototype exists to expose. The honest refusal is the feature.
  if q_exact is null then
    return jsonb_build_object(
      'band',  'unknown_query',
      'query', q_raw,
      'why',   'This query is not in the search log, so we cannot show what this system would do '
               || 'with it. Embeddings are precomputed for the 613 logged queries only — we are '
               || 'not going to guess and present the guess as a result.',
      'logged_queries', (select count(*) from public.query_embeddings)
    );
  end if;

  -- Similarity against THIS MARKET's services only. D-A: market and city are
  -- structured filters and live here, never inside the vector.
  with scored as (
    select s.service_id, s.title, s.doc, s.description, s.category_l2,
           (1 - (se.embedding operator(extensions.<=>) q_emb))::numeric as sim
    from public.services s
    join public.service_embeddings se on se.service_id = s.service_id
    where s.market = p_market
  )
  select max(sim),
         (select to_jsonb(x) from (
            select title, doc, round(sim, 4) as similarity from scored order by sim desc limit 1
          ) x)
    into v_max, v_matched
  from scored;

  v_band := case
              when v_max >= cfg.high then 'confident'
              when v_max >= cfg.low  then 'adjacent'
              else 'abstain'
            end;

  -- Part A's verdict, independent of anything above. Null when this market never
  -- logged this query — which is a fact, not a failure.
  select * into v_class
  from public.query_classes qc
  where qc.market = p_market and qc.q = q_exact;

  -- Deals are only shown above LOW. Below it the honest answer is nothing, and
  -- shipping a list anyway is the defect.
  if v_band <> 'abstain' then
    select coalesce(jsonb_agg(r order by r->>'similarity' desc), '[]'::jsonb) into v_results
    from (
      select to_jsonb(t) as r from (
        select d.deal_id, d.title, d.price_usd, d.rating, d.num_ratings, d.is_bookable, d.city,
               round((1 - (se.embedding operator(extensions.<=>) q_emb))::numeric, 4) as similarity
        from public.deals d
        join public.services s
          on s.market = d.market and s.title = d.title
        join public.service_embeddings se on se.service_id = s.service_id
        where d.market = p_market and d.city = p_city
          and 1 - (se.embedding operator(extensions.<=>) q_emb) >= cfg.low
        order by se.embedding operator(extensions.<=>) q_emb, d.rating desc nulls last
        limit p_limit
      ) t
    ) z;
    -- Counted before the limit. near_empty must describe what the CATALOGUE has,
    -- not how many rows the caller asked for — computing it from the limited set
    -- makes every small page look like a near-empty state, which is the one
    -- signal on this page that has to stay meaningful.
    select count(*) into v_available
    from public.deals d
    join public.services s on s.market = d.market and s.title = d.title
    join public.service_embeddings se on se.service_id = s.service_id
    where d.market = p_market and d.city = p_city
      and (1 - (se.embedding operator(extensions.<=>) q_emb))::numeric >= cfg.low;
  else
    v_results := '[]'::jsonb;
  end if;

  -- §5: an abstention IS a demand signal. Recorded as source='live' so it never
  -- mixes with the seeded month, and n=1 so a click cannot inflate the brief.
  if v_band = 'abstain' then
    insert into public.demand_events (market, city, concept, raw_query, source, n)
    values (p_market, p_city, v_class.concept, q_exact, 'live', 1);
  end if;

  return jsonb_build_object(
    'band',            v_band,
    'query',           q_raw,
    'resolved_to',     q_exact,
    'normalised',      v_normalised,     -- disclosed, never silent
    'max_similarity',  round(v_max, 4),
    'results',         v_results,
    'result_count',    jsonb_array_length(v_results),
    'available',       v_available,
    -- 1-2 results converts like zero (FINDINGS §1), so the count is a state in its
    -- own right and the caller must not render it as an ordinary results page.
    'near_empty',      v_available between 1 and 2,
    'staff', jsonb_build_object(
      'matched',         v_matched,
      'low',             cfg.low,
      'high',            cfg.high,
      'model',           cfg.model,
      'calibrated_on',   cfg.calibrated_on,
      'false_confident', cfg.false_confident,
      'false_abstain',   cfg.false_abstain,
      'part_a_class',    v_class.failure_class,
      'part_a_coverage', v_class.coverage,
      'part_a_concept',  v_class.concept,
      'thin_label',      v_class.thin_n,
      'searches',        v_class.searches,
      'dead_ends',       v_class.deads,
      -- The row the staff panel exists for. Part A says stocked; the band may say
      -- abstain. Surfacing that beats tuning it away.
      'band_agrees_with_part_a',
        case when v_class.coverage is null then null
             else (v_class.coverage = 'absent') = (v_band = 'abstain') end
    )
  );
end;
$function$;

COMMENT ON FUNCTION public.search_deals(text,text,text,integer) IS 'Returns the band AND Part A''s class, because they answer different questions: the band is what this system decided just now, the class is what the analysis established. Showing both side by side is the "show your working" deliverable. Abstains below search_config.low and writes a demand row when it does; refuses by name for any query outside the logged 613.';

REVOKE ALL ON FUNCTION public.search_deals(text, text, text, integer) FROM PUBLIC;

GRANT ALL ON FUNCTION public.search_deals(text, text, text, integer) TO anon;

GRANT ALL ON FUNCTION public.search_deals(text, text, text, integer) TO authenticated;

CREATE TABLE public.search_config (
  singleton       boolean DEFAULT true NOT NULL,
  low             numeric NOT NULL,
  high            numeric NOT NULL,
  model           text    NOT NULL,
  calibrated_on   date    NOT NULL,
  n_labelled      integer NOT NULL,
  false_confident numeric NOT NULL,
  false_abstain   numeric NOT NULL,
  note            text    NOT NULL
);

COMMENT ON TABLE public.search_config IS 'One row. Thresholds with the provenance attached, so a number in the UI can be traced to the sweep that produced it and the model it was calibrated against.';

ALTER TABLE public.search_config
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.search_config
  ADD CONSTRAINT search_config_pkey PRIMARY KEY (singleton);

ALTER TABLE public.search_config
  ADD CONSTRAINT search_config_singleton_check CHECK (singleton);

GRANT SELECT ON public.search_config TO anon;

GRANT SELECT ON public.search_config TO authenticated;

GRANT MAINTAIN, REFERENCES, TRIGGER, TRUNCATE ON public.search_config TO service_role;

CREATE POLICY search_config_read ON public.search_config
  FOR SELECT
  TO anon, authenticated
  USING (true);
