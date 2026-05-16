import * as Yup from "yup";
import type { ForgotPasswordCredentials } from "@/types/user";

export const forgotPasswordSchema = Yup.object({
  email: Yup.string()
    .trim()
    .required("Email is required")
    .email("Enter a valid email address"),
});

export type ForgotPasswordFormValues = ForgotPasswordCredentials;

export const forgotPasswordInitialValues: ForgotPasswordFormValues = {
  email: "",
};
