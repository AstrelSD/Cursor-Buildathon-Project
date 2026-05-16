-- Allow all Sri Lanka districts on profiles (registration form is source of truth).
alter table public.profiles drop constraint if exists profiles_district_check;

alter table public.profiles add constraint profiles_district_check check (
  district in (
    'Ampara', 'Anuradhapura', 'Badulla', 'Batticaloa', 'Colombo', 'Galle',
    'Gampaha', 'Hambantota', 'Jaffna', 'Kalutara', 'Kandy', 'Kegalle',
    'Kilinochchi', 'Kurunegala', 'Mannar', 'Matale', 'Matara', 'Monaragala',
    'Mullaitivu', 'Nuwaraliya', 'Nuwara Eliya', 'Polonnaruwa', 'Puttalam',
    'Ratnapura', 'Trincomalee', 'Vavuniya'
  )
);
