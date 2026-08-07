-- Query-side vectors. 007-embeddings/SPEC.md decision E4.
--
-- KEYED ON `q` ALONE, not (market, q). The same string encodes identically in
-- every market, and 58 of the 613 distinct queries appear in more than one. So
-- this is 613 rows serving 751 (market, q) pairs, and the market filter lives in
-- the join — consistent with D-A, which keeps market and city out of the vector
-- because they are structured filters.
--
-- WHAT THIS ENABLES AND WHAT IT DOES NOT. It covers the 613 queries the log
-- actually contains, which is every demo and every claim Part A makes. A query
-- the log never saw has no row here, and the prototype must SAY SO rather than
-- return the nearest logged query's results — that would be silent substitution,
-- the exact failure this package exists to expose (SPEC E6).

create table public.query_embeddings (
  q         text primary key,
  embedding extensions.vector(384) not null,
  model     text not null,
  built_at  timestamptz not null default now()
);

comment on table public.query_embeddings is
  '613 rows — the distinct queries in search_log.csv, lowercased and trimmed exactly as '
  'query_classes.q stores them. Not (market, q): the text is market-independent. A query absent '
  'from this table is refused by name, never silently substituted.';

comment on column public.query_embeddings.model is
  'The encoder that produced this vector. Recorded because a calibrated threshold is only '
  'meaningful against a named model — swapping it invalidates the sweep rather than shifting it.';

-- No index, deliberately: at this size an exact scan is faster AND has exact
-- recall, while HNSW is approximate and would trade recall for nothing.

-- RLS on, NO policy and NO grant — two independent locks, same posture as
-- service_embeddings. Vectors are server-side only; the search RPC will be
-- security definer and read them under its own privileges.
alter table public.query_embeddings enable row level security;

-- Belt and braces against the defect found in 20260806222319: local and remote
-- carry opposite default ACLs, so state the end result absolutely rather than
-- trusting whatever this target happens to grant on CREATE TABLE.
revoke all on public.query_embeddings from anon, authenticated;
