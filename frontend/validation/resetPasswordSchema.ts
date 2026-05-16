import * as Yup from "yup";
import type { ResetPasswordCredentials } from "@/types/user";

export const resetPasswordSchema = Yup.object({
  password: Yup.string()
    .required("Password is required")
    .min(6, "Password must be at least 6 characters"),
  confirmPassword: Yup.string()
    .required("Please confirm your password")
    .oneOf([Yup.ref("password")], "Passwords must match"),
});

export type ResetPasswordFormValues = ResetPasswordCredentials;

export const resetPasswordInitialValues: ResetPasswordFormValues = {
  password: "",
  confirmPassword: "",
};
