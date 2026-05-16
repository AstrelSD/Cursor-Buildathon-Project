import { createClient } from "@/lib/supabase/client";

export const signInWithEmail = async (email: string, password: string) => {
  const supabase = createClient();
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    throw error;
  }

  return data;
};

type SignUpMetadata = {
  firstName: string;
  lastName: string;
  phone: string;
  address: string;
};

export const signUpWithEmail = async (
  email: string,
  password: string,
  metadata: SignUpMetadata,
) => {
  const supabase = createClient();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        first_name: metadata.firstName,
        last_name: metadata.lastName,
        phone: metadata.phone,
        address: metadata.address,
        full_name: `${metadata.firstName} ${metadata.lastName}`.trim(),
      },
    },
  });

  if (error) {
    throw error;
  }

  return data;
};

/** Sends a one-time passcode to the user's email for password recovery. */
export const sendPasswordResetOtp = async (email: string) => {
  const supabase = createClient();
  const { data, error } = await supabase.auth.signInWithOtp({
    email,
    options: {
      shouldCreateUser: false,
    },
  });

  if (error) {
    throw error;
  }

  return data;
};

/** Verifies the OTP and establishes a recovery session. */
export const verifyPasswordResetOtp = async (email: string, otp: string) => {
  const supabase = createClient();
  const { data, error } = await supabase.auth.verifyOtp({
    email,
    token: otp,
    type: "email",
  });

  if (error) {
    throw error;
  }

  return data;
};

/** Updates password after OTP verification (active session required). */
export const updatePassword = async (password: string) => {
  const supabase = createClient();
  const { data, error } = await supabase.auth.updateUser({ password });

  if (error) {
    throw error;
  }

  return data;
};

export const signOut = async () => {
  const supabase = createClient();
  const { error } = await supabase.auth.signOut();

  if (error) {
    throw error;
  }
};
