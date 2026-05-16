-- Allow apply flow: draft loan insert + evidence uploads via anon key (hackathon demo)
drop policy if exists "apply_insert_loans" on public.loans;
create policy "apply_insert_loans"
  on public.loans
  for insert
  with check (true);

drop policy if exists "apply_update_own_loans" on public.loans;
create policy "apply_update_own_loans"
  on public.loans
  for update
  using (true)
  with check (true);

insert into storage.buckets (id, name, public)
values ('loan-evidence', 'loan-evidence', true)
on conflict (id) do update set public = true;

drop policy if exists "apply_upload_evidence" on storage.objects;
create policy "apply_upload_evidence"
  on storage.objects
  for insert
  to anon, authenticated
  with check (bucket_id = 'loan-evidence');

drop policy if exists "apply_read_evidence" on storage.objects;
create policy "apply_read_evidence"
  on storage.objects
  for select
  to anon, authenticated
  using (bucket_id = 'loan-evidence');
