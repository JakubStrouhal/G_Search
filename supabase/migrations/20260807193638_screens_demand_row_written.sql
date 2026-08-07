-- Migration unit 1: schema_changes
-- Transaction mode: transactional
-- Boundary reason: default

SET check_function_bodies = false;

CREATE OR REPLACE FUNCTION public.search_deals (
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
  v_logged_here    boolean := false;
  v_results        jsonb;
  v_matched        jsonb;
  v_alternatives   jsonb := '[]'::jsonb;
  v_alt_max        numeric;
  v_available      integer := 0;   -- matches above LOW, BEFORE p_limit
  v_city_empty     boolean := false;
  v_demand_source  text;            -- null when no row was written
begin
  select * into cfg from public.search_config;

  -- Fail loudly on a missing config. Without this the NULL thresholds make every
  -- comparison NULL, the CASE falls through to its ELSE, and the function abstains
  -- on ABSOLUTELY EVERYTHING while returning 200. A search engine that silently
  -- answers "we have nothing" to every query is the worst possible failure here,
  -- and it would look like a working deploy. Found exactly this way: `db pull`
  -- regenerates schema and not data, so a rebuilt migration dropped the row.
  -- alt_floor joins the guard for the same reason: a null floor makes
  -- alternatives_above_floor null, and the abstain state would then show a
  -- manicure as the closest thing to paintball.
  if cfg.low is null or cfg.high is null or cfg.alt_floor is null then
    raise exception 'search_config is empty or incomplete: thresholds are not loaded. '
                    'Run `python3 supabase/build_seed.py && npx supabase db reset`. '
                    'Refusing to answer rather than silently abstaining on every query.';
  end if;

  if q_raw is null or q_raw = '' then
    return jsonb_build_object('band', 'empty', 'query', p_query,
                              'demand_row_written', false);
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
      'logged_queries', (select count(*) from public.query_embeddings),
      -- Stated, not implied by absence. A refusal writes NO demand row: an
      -- unlogged query has no concept to attribute, so counting it would let the
      -- acquisition brief silently over-count. The staff panel says so.
      'demand_row_written', false
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

  -- ALTERNATIVES — computed on every band, rendered only below `confident`.
  --
  -- WHAT THESE ARE AND ARE NOT. They are catalogue titles ranked by cosine
  -- distance from the query vector, restricted to titles THIS CITY ACTUALLY
  -- STOCKS. They are NOT measured relevance and NOT evidence about which deals
  -- any query ever returned — the log carries results_shown as a bare count and
  -- there is no query->deal mapping. The similarity ships with every row so the
  -- caller cannot present them as an answer.
  --
  -- "Stocked in p_city" is an EXISTS predicate rather than a join-and-group,
  -- because it is the one property that has to survive a reseed (010 SPEC,
  -- "What would make this spec wrong").
  select coalesce(jsonb_agg(to_jsonb(t) order by t.similarity desc), '[]'::jsonb),
         max(t.similarity)
    into v_alternatives, v_alt_max
  from (
    select s.title,
           s.category_l2,
           round((1 - (se.embedding operator(extensions.<=>) q_emb))::numeric, 4) as similarity,
           (select count(*)::integer
              from public.deals d
             where d.market = s.market and d.title = s.title and d.city = p_city) as deal_count
    from public.services s
    join public.service_embeddings se on se.service_id = s.service_id
    where s.market = p_market
      and exists (select 1
                    from public.deals d
                   where d.market = s.market and d.title = s.title and d.city = p_city)
    order by se.embedding operator(extensions.<=>) q_emb
    limit 3
  ) t;

  -- Part A's verdict, independent of anything above. Null when this market never
  -- logged this query — which is a fact, not a failure.
  select * into v_class
  from public.query_classes qc
  where qc.market = p_market and qc.q = q_exact;
  -- Assigned IMMEDIATELY: the next statement would reset FOUND.
  --
  -- WHY THIS FLAG EXISTS. query_embeddings is keyed on `q` alone (613 rows) while
  -- query_classes is keyed on (market, q) (751 rows), so a query logged in one
  -- market resolves in all five. `helicopter tour` in DE is real: it embeds, it
  -- abstains, and Part A has no verdict on it HERE. That is a fact about the data,
  -- not a failure — but three nulls do not say so, and a caller left to infer it
  -- would print a June figure it does not have. The demand row is still written:
  -- someone did search for it, raw_query preserves what they typed, and dropping
  -- real demand to keep a column tidy would be the wrong trade.
  v_logged_here := found;

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

  -- THE CITY-EMPTY HOLE, closed. near_empty is 1-2 BY DESIGN — FINDINGS §1 shows
  -- 1-2 converts at 1.7% like zero, which is why it is its own state, and calling
  -- a state "near-empty" when it fires on zero would be a lie in a variable name.
  -- But that left `available = 0` in a NON-abstain band falling through the
  -- precedence rule entirely: 424 of 12,260 combos (92 confident, 332 adjacent)
  -- where the market scores above LOW and the user's city stocks nothing, which
  -- rendered as `Results for "X"` over an empty grid — the silent empty page this
  -- build exists to prevent. It gets its own flag rather than a widened one.
  --
  -- PRECEDENCE, exhaustive: unknown_query -> empty -> abstain -> city_empty ->
  -- near_empty -> band. city_empty and near_empty are mutually exclusive by
  -- construction (0 against 1-2), so the order between them never binds.
  v_city_empty := v_band <> 'abstain' and v_available = 0;

  -- §5: a dead end IS a demand signal, and there are two different dead ends here.
  -- 'live'       = the market had nothing anywhere      -> merchant acquisition
  -- 'city_empty' = the market had something, this city stocked none of it
  -- They are recorded under different sources because they have different owners
  -- and the brief displays live_abstentions as its own number; folding city-empty
  -- into it would mislabel a figure already on screen. n=1 either way, so a click
  -- cannot inflate the seeded month. Both reach the table because this function is
  -- SECURITY DEFINER, owned by postgres, and demand_events is not FORCE RLS — the
  -- append policy permits notify_me ONLY, so neither can be forged over REST.
  -- concept is null when Part A never logged this query in this market (above);
  -- the row is still worth keeping, and raw_query carries what was typed.
  --
  -- ONE PLACE DECIDES, AND IT REPORTS WHAT IT DECIDED. The response carries
  -- `demand_row_written` and `staff.demand_source` because a caller that
  -- re-derives "was a row written?" from the band will get it wrong the moment a
  -- new writing branch appears -- which is exactly what happened: the staff panel
  -- printed "not written - not an abstention" on city-empty responses while this
  -- function was writing one. Same reasoning as alternatives_above_floor.
  v_demand_source := case when v_band = 'abstain' then 'live'
                          when v_city_empty     then 'city_empty' end;

  if v_demand_source is not null then
    insert into public.demand_events (market, city, concept, raw_query, source, n)
    values (p_market, p_city, v_class.concept, q_exact, v_demand_source, 1);
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
    -- The market scored above LOW but this city stocks nothing. Renders as its own
    -- honest-nothing state, NEVER as an empty results grid — and never as a
    -- cross-city offer: that copy was cut (010 SPEC) and INDEX #12 records it was
    -- false for 315 of 321 rows when it shipped once before. The user is told
    -- there is nothing here, full stop; the market-vs-city contrast is staff-only.
    'city_empty',      v_city_empty,
    'demand_row_written', v_demand_source is not null,
    'alternatives',    v_alternatives,
    -- The floor comparison is made HERE, once, so the screen and the staff panel
    -- cannot drift apart by re-implementing it (010 SPEC decision 18).
    'alternatives_above_floor', coalesce(v_alt_max >= cfg.alt_floor, false),
    'staff', jsonb_build_object(
      'matched',         v_matched,
      'low',             cfg.low,
      'high',            cfg.high,
      'alt_floor',       cfg.alt_floor,
      -- Deliberately the same number as the top-level max_similarity, under a name
      -- that states its SCOPE. The scored set is filtered on market only, never on
      -- city, so this is what the market's best document scored — and the contrast
      -- with `available` (what this city actually stocks) is the whole point of the
      -- city-empty state: market 0.62, city 0. Staff panel only.
      'market_max_similarity', round(v_max, 4),
      -- 'live' = the market had nothing anywhere; 'city_empty' = the market had
      -- something, this city stocked none of it; null = nothing was written.
      'demand_source',   v_demand_source,
      'alt_max',         v_alt_max,
      'model',           cfg.model,
      'calibrated_on',   cfg.calibrated_on,
      'false_confident', cfg.false_confident,
      'false_abstain',   cfg.false_abstain,
      -- False means: in the logged 613, but NOT logged in THIS market, so Part A
      -- has no verdict here. The caller keys "N searches in June" off this and
      -- prints nothing when it is false — no row, no number.
      'part_a_logged_here', v_logged_here,
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

-- No ACL block in this migration, deliberately, and the reason is worth stating
-- so its absence does not read as the 4.1 oversight: this file creates no
-- grantable object. search_deals is CREATE OR REPLACE, which PRESERVES the
-- function's existing ACL, and nothing else is dropped or recreated. The
-- end-state ACL remains the one 20260807175250 states absolutely.
