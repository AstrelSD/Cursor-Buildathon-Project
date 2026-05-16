"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Formik, Form, type FormikHelpers } from "formik";
import { ArrowRight, Mail } from "lucide-react";
import { AuthFormLayout } from "@/components/auth/AuthFormLayout";
import { FormAlert, FormTextField } from "@/components/auth/form-fields";
import CommonButton from "@/components/ui/button";
import { PATH_LOGIN, PATH_OTP } from "@/constants/routes";
import type { ForgotPasswordCredentials } from "@/types/user";
import { sendPasswordResetOtp } from "@/utils/authFunctions";
import { getAuthErrorMessage } from "@/utils/authError";
import { formStyles } from "@/utils/formFieldClass";
import {
  forgotPasswordInitialValues,
  forgotPasswordSchema,
} from "@/validation/forgotPasswordSchema";

export default function ForgotPasswordPage() {
  const router = useRouter();

  const handleSubmit = async (
    values: ForgotPasswordCredentials,
    { setSubmitting, setStatus }: FormikHelpers<ForgotPasswordCredentials>,
  ) => {
    setStatus(undefined);
    try {
      await sendPasswordResetOtp(values.email);
      router.push(
        `${PATH_OTP}?email=${encodeURIComponent(values.email)}`,
      );
    } catch (err: unknown) {
      setStatus(
        getAuthErrorMessage(err, "Could not send OTP. Please try again."),
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthFormLayout subtitle="Enter your email and we'll send a one-time passcode to reset your password.">
      <Formik
        initialValues={forgotPasswordInitialValues}
        validationSchema={forgotPasswordSchema}
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

            <CommonButton
              type="submit"
              loading={isSubmitting}
              disabled={isSubmitting}
              className={formStyles.submitButton}
              icon={<ArrowRight className="h-5 w-5" />}
              iconPosition="right"
            >
              Request OTP
            </CommonButton>
          </Form>
        )}
      </Formik>

      <p className={formStyles.footerLink}>
        Remember your password?{" "}
        <Link href={PATH_LOGIN} className={formStyles.link}>
          Log in
        </Link>
      </p>
    </AuthFormLayout>
  );
}
