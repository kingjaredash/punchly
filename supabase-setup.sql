-- Punchly sync — paste this whole file into the Supabase SQL editor and Run.
--
-- Security model: the table itself is unreachable from the browser. RLS is on
-- with no policies, and the anon role has no grants on it, so the public anon
-- key cannot select, insert or dump anything. All access goes through the two
-- functions below, and both demand the ledger id — a 128-bit random string
-- that never leaves your devices. Without it there is nothing to read.

create table if not exists public.punchly_entries (
  ledger_id  text    not null,
  id         text    not null,
  data       jsonb   not null default '{}'::jsonb,
  updated_at bigint  not null,
  deleted    boolean not null default false,
  primary key (ledger_id, id)
);

alter table public.punchly_entries enable row level security;
revoke all on public.punchly_entries from anon, authenticated;

-- Read one ledger.
create or replace function public.punchly_pull(p_ledger text)
returns table (id text, data jsonb, updated_at bigint, deleted boolean)
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_ledger is null or length(p_ledger) < 24 then
    raise exception 'bad ledger id';
  end if;
  return query
    select e.id, e.data, e.updated_at, e.deleted
    from public.punchly_entries e
    where e.ledger_id = p_ledger;
end;
$$;

-- Write a batch. Last writer wins per entry, decided by the caller's
-- timestamp, so a phone coming back online cannot clobber newer edits.
create or replace function public.punchly_push(p_ledger text, p_rows jsonb)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  n integer := 0;
begin
  if p_ledger is null or length(p_ledger) < 24 then
    raise exception 'bad ledger id';
  end if;
  if jsonb_typeof(p_rows) <> 'array' then
    raise exception 'rows must be an array';
  end if;

  insert into public.punchly_entries as m (ledger_id, id, data, updated_at, deleted)
  select p_ledger,
         r->>'id',
         coalesce(r->'data', '{}'::jsonb),
         (r->>'updated_at')::bigint,
         coalesce((r->>'deleted')::boolean, false)
  from jsonb_array_elements(p_rows) as r
  where r->>'id' is not null
  on conflict (ledger_id, id) do update
     set data       = excluded.data,
         updated_at = excluded.updated_at,
         deleted    = excluded.deleted
   where excluded.updated_at > m.updated_at;

  get diagnostics n = row_count;
  return n;
end;
$$;

grant execute on function public.punchly_pull(text)        to anon;
grant execute on function public.punchly_push(text, jsonb) to anon;
