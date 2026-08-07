-- Make table privileges DETERMINISTIC, independent of the target's default ACLs.
--
-- WHY THIS EXISTS. The initial migration only ADDED grants, which meant the
-- resulting security depended on whatever `alter default privileges` the target
-- database happened to carry. The two targets carry OPPOSITE defaults:
--
--   local  (supabase CLI, current)  anon=Dxtm   -- withholds a/r/w/d, grants TRUNCATE
--   remote (project ewknlggenhrlftdukwme) anon=arwd  -- auto-grants SELECT/INSERT/UPDATE/DELETE
--
-- So the same migration produced a locked-down local database and a wide-open
-- remote one: after the first push, `anon` held DELETE, INSERT, UPDATE and SELECT
-- on all seven tables, INCLUDING service_embeddings, which locally has no grant
-- at all. RLS was still denying the actual operations (enabled + no matching
-- policy = deny), so nothing was exploitable — but defence-in-depth had collapsed
-- to a single layer, and one permissive policy added later would have become a
-- full breach.
--
-- The deeper defect: verifying security on the local database proved NOTHING about
-- the remote. This migration removes that gap by stating the end state absolutely
-- rather than incrementally.
--
-- REVOKE ALL first, then grant back exactly the intended set. Idempotent, and it
-- lands identically on any target regardless of what it started with.

revoke all on all tables in schema public from anon, authenticated;

-- Public read. The catalogue and the Part A contract are the published artifact.
grant select on public.cities             to anon, authenticated;
grant select on public.deals              to anon, authenticated;
grant select on public.services           to anon, authenticated;
grant select on public.service_concepts   to anon, authenticated;
grant select on public.query_classes      to anon, authenticated;
grant select on public.v_city_inventory   to anon, authenticated;
grant select on public.v_demand_by_cell   to anon, authenticated;

-- The only write path in the entire schema. The RLS policy's `with check` pins
-- source='live' and n=1 so the browser cannot forge seed-weighted rows.
grant select, insert on public.demand_events to anon, authenticated;

-- service_embeddings: deliberately no grant. Combined with RLS-enabled-and-no-policy
-- that is two independent locks. The search RPC (SPEC §10 step 4) will be security
-- definer and read it under its own privileges.

-- Future objects: no ambient access. Every new table must be granted explicitly,
-- on every target, forever. This is what makes the guarantee portable.
alter default privileges in schema public revoke all on tables from anon, authenticated;
