-- Farmer payout account on profile + loan repayment tracking
alter table public.profiles
  add column if not exists payout_account_number text,
  add column if not exists payout_bank_code text;

alter table public.loans drop constraint if exists loans_status_check;

alter table public.loans
  add column if not exists repayment_method text check (
    repayment_method is null or repayment_method in ('qr', 'cefts')
  ),
  add column if not exists repayment_reference text,
  add column if not exists repayment_qr_request_ref text,
  add column if not exists repaid_at timestamp with time zone;

alter table public.loans
  add constraint loans_status_check check (
    status in (
      'draft',
      'analyzing',
      'underwriting',
      'approved',
      'disbursed',
      'repayment_pending',
      'repaid',
      'rejected'
    )
  );

drop policy if exists "users_update_own_profile" on public.profiles;
create policy "users_update_own_profile"
  on public.profiles
  for update
  to authenticated
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- Extend signup trigger to persist optional payout account from auth metadata
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  meta jsonb;
  phone_val text;
  district_val text;
  full_name_val text;
  payout_acct text;
  payout_bank text;
begin
  meta := coalesce(new.raw_user_meta_data, '{}'::jsonb);

  phone_val := nullif(trim(meta->>'phone'), '');
  if phone_val is null or phone_val !~ '^\+94[0-9]{9}$' then
    raise exception 'Registration requires a valid Sri Lankan phone (+94 followed by 9 digits).';
  end if;

  district_val := nullif(trim(meta->>'district'), '');
  if district_val is null or length(district_val) < 2 then
    raise exception 'Registration requires a farm district.';
  end if;

  full_name_val := nullif(trim(meta->>'full_name'), '');
  if full_name_val is null then
    full_name_val := trim(
      coalesce(meta->>'first_name', '') || ' ' || coalesce(meta->>'last_name', '')
    );
  end if;
  if full_name_val = '' then
    raise exception 'Registration requires a full name.';
  end if;

  payout_acct := nullif(trim(meta->>'payout_account_number'), '');
  payout_bank := nullif(trim(meta->>'payout_bank_code'), '');

  insert into public.profiles (
    id,
    full_name,
    phone,
    district,
    payout_account_number,
    payout_bank_code
  )
  values (
    new.id,
    full_name_val,
    phone_val,
    district_val,
    payout_acct,
    payout_bank
  )
  on conflict (id) do update set
    full_name = excluded.full_name,
    phone = excluded.phone,
    district = excluded.district,
    payout_account_number = coalesce(
      excluded.payout_account_number,
      public.profiles.payout_account_number
    ),
    payout_bank_code = coalesce(
      excluded.payout_bank_code,
      public.profiles.payout_bank_code
    );

  return new;
end;
$$;
