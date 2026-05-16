-- Auto-create public.profiles when a Supabase Auth user registers (metadata from signup form).
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
  -- District whitelist is enforced by profiles.district check constraint (see expand migration).

  full_name_val := nullif(trim(meta->>'full_name'), '');
  if full_name_val is null then
    full_name_val := trim(
      coalesce(meta->>'first_name', '') || ' ' || coalesce(meta->>'last_name', '')
    );
  end if;
  if full_name_val = '' then
    raise exception 'Registration requires a full name.';
  end if;

  insert into public.profiles (id, full_name, phone, district)
  values (new.id, full_name_val, phone_val, district_val)
  on conflict (id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
