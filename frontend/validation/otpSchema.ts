import * as Yup from "yup";
import type { OtpCredentials } from "@/types/user";

export const otpSchema = Yup.object({
  otp: Yup.string()
    .trim()
    .required("OTP is required")
    .min(8, "OTP must be at least 8 characters"),
});

export type OtpFormValues = OtpCredentials;

export const otpInitialValues: OtpFormValues = {
  otp: "",
};
