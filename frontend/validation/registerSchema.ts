import * as Yup from "yup";
import type { RegisterCredentials } from "@/types/user";

const sriLankanPhoneRegex = /^\+94[0-9]{9}$/;

export const registerSchema = Yup.object({
  firstName: Yup.string()
    .trim()
    .required("First name is required")
    .min(2, "First name must be at least 2 characters"),
  lastName: Yup.string()
    .trim()
    .required("Last name is required")
    .min(2, "Last name must be at least 2 characters"),
  email: Yup.string()
    .trim()
    .required("Email is required")
    .email("Enter a valid email address"),
  phone: Yup.string()
    .trim()
    .required("Phone number is required")
    .matches(
      sriLankanPhoneRegex,
      "Use Sri Lankan format: +94 followed by 9 digits",
    ),
  address: Yup.string()
    .trim()
    .required("Address is required")
    .min(5, "Address must be at least 5 characters"),
  password: Yup.string()
    .required("Password is required")
    .min(6, "Password must be at least 6 characters"),
  confirmPassword: Yup.string()
    .required("Please confirm your password")
    .oneOf([Yup.ref("password")], "Passwords must match"),
});

export type RegisterFormValues = RegisterCredentials;

export const registerInitialValues: RegisterFormValues = {
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  address: "",
  password: "",
  confirmPassword: "",
};
