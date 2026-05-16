export type LoginCredentials = {
  email: string;
  password: string;
};

export type RegisterCredentials = {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  district: string;
  address: string;
  password: string;
  confirmPassword: string;
};

export type ForgotPasswordCredentials = {
  email: string;
};

export type OtpCredentials = {
  otp: string;
};

export type ResetPasswordCredentials = {
  password: string;
  confirmPassword: string;
};

export type IUser = {
  id: string;
  email: string;
  fullName: string;
  phone?: string;
  district?: string;
  address?: string;
  createdAt?: string;
};
