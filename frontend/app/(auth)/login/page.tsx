"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Formik, Form, type FormikHelpers } from "formik";
import { ArrowRight, Mail } from "lucide-react";
import { AuthFormLayout } from "@/components/auth/AuthFormLayout";
import {
  FormAlert,
  FormPasswordField,
  FormTextField,
} from "@/components/auth/form-fields";
import CommonButton from "@/components/ui/button";
import {
  PATH_DASHBOARD,
  PATH_FORGOT_PASSWORD,
  PATH_REGISTER,
} from "@/constants/routes";
import type { LoginCredentials } from "@/types/user";
import { signInWithEmail } from "@/utils/authFunctions";
import { getAuthErrorMessage } from "@/utils/authError";
import { formStyles } from "@/utils/formFieldClass";
import {
  loginInitialValues,
  loginSchema,
} from "@/validation/loginSchema";

export default function LoginPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (
    values: LoginCredentials,
    { setSubmitting, setStatus }: FormikHelpers<LoginCredentials>,
  ) => {
    setStatus(undefined);
    try {
      await signInWithEmail(values.email, values.password);
      router.push(PATH_DASHBOARD);
    } catch (err: unknown) {
      setStatus(getAuthErrorMessage(err, "Login failed. Please try again."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthFormLayout subtitle="Secure access to your farm's financial future.">
      <Formik
        initialValues={loginInitialValues}
        validationSchema={loginSchema}
        onSubmit={handleSubmit}
      >
        {({ isSubmitting, status }) => (
          <Form className="mt-8 space-y-5" noValidate>
            <FormAlert message={status} />

            <FormTextField
              name="email"
              id="email"
              label="Email"
              type="email"
              placeholder="Enter your email"
              autoComplete="email"
              icon={Mail}
            />

            <FormPasswordField
              name="password"
              id="password"
              label="Password"
              placeholder="Enter your password"
              autoComplete="current-password"
              show={showPassword}
              onToggle={() => setShowPassword((v) => !v)}
            />

            <CommonButton
              type="submit"
              loading={isSubmitting}
              disabled={isSubmitting}
              className={formStyles.submitButton}
              icon={<ArrowRight className="h-5 w-5" />}
              iconPosition="right"
            >
              Log In
            </CommonButton>
          </Form>
        )}
      </Formik>

      <p className="mt-6 text-center text-sm text-gray-500">
        <Link href={PATH_FORGOT_PASSWORD} className="hover:text-[#2E7D32]">
          Forgot Password?
        </Link>
      </p>

      <p className={formStyles.footerLink}>
        Don&apos;t have an account?{" "}
        <Link href={PATH_REGISTER} className={formStyles.link}>
          Register
        </Link>
      </p>
    </AuthFormLayout>
  );
}
