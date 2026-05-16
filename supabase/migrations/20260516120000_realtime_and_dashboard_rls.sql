-- Realtime broadcasts for UnderwritingTerminal (Phase 4)
alter table public.loans replica identity full;

do $$
begin
  alter publication supabase_realtime add table public.loans;
exception
  when duplicate_object then null;
end $$;

-- Hackathon demo: allow dashboard reads via anon key (no auth UI yet)
alter table public.loans enable row level security;
alter table public.profiles enable row level security;

drop policy if exists "dashboard_read_loans" on public.loans;
create policy "dashboard_read_loans"
  on public.loans
  for select
  using (true);

drop policy if exists "dashboard_read_profiles" on public.profiles;
create policy "dashboard_read_profiles"
  on public.profiles
  for select
  using (true);
