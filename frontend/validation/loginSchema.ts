import * as Yup from "yup";
import type { LoginCredentials } from "@/types/user";

export const loginSchema = Yup.object({
  email: Yup.string()
    .trim()
    .required("Email is required")
    .email("Enter a valid email address"),
  password: Yup.string()
    .required("Password is required")
    .min(6, "Password must be at least 6 characters"),
});

export type LoginFormValues = LoginCredentials;

export const loginInitialValues: LoginFormValues = {
  email: "",
  password: "",
};
