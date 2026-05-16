import type { User as SupabaseUser } from "@supabase/supabase-js";
import type { IUser } from "@/types/user";

export function mapSupabaseUser(supabaseUser: SupabaseUser): IUser {
  const meta = supabaseUser.user_metadata ?? {};
  const firstName = meta.first_name as string | undefined;
  const lastName = meta.last_name as string | undefined;
  const fullName =
    (meta.full_name as string | undefined) ||
    [firstName, lastName].filter(Boolean).join(" ") ||
    supabaseUser.email?.split("@")[0] ||
    "";

  return {
    id: supabaseUser.id,
    email: supabaseUser.email ?? "",
    fullName,
    phone: meta.phone as string | undefined,
    address: meta.address as string | undefined,
    district: meta.district as string | undefined,
    createdAt: supabaseUser.created_at,
  };
}
