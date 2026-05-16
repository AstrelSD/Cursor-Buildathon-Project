"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Formik, Form, type FormikHelpers } from "formik";
import { ArrowRight, KeyRound } from "lucide-react";
import { AuthFormLayout } from "@/components/auth/AuthFormLayout";
import { FormAlert, FormTextField } from "@/components/auth/form-fields";
import CommonButton from "@/components/ui/button";
import {
  PATH_FORGOT_PASSWORD,
  PATH_LOGIN,
  PATH_RESET_PASSWORD,
} from "@/constants/routes";
import type { OtpCredentials } from "@/types/user";
import { verifyPasswordResetOtp } from "@/utils/authFunctions";
import { getAuthErrorMessage } from "@/utils/authError";
import { formStyles } from "@/utils/formFieldClass";
import { otpInitialValues, otpSchema } from "@/validation/otpSchema";

function OtpForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const emailFromQuery = searchParams.get("email") ?? "";

  const handleSubmit = async (
    values: OtpCredentials,
    { setSubmitting, setStatus }: FormikHelpers<OtpCredentials>,
  ) => {
    setStatus(undefined);
    try {
      await verifyPasswordResetOtp(emailFromQuery, values.otp);
      sessionStorage.setItem("resetEmail", emailFromQuery);
      router.push(PATH_RESET_PASSWORD);
    } catch (err: unknown) {
      setStatus(
        getAuthErrorMessage(
          err,
          "Invalid OTP. Please check the code and try again.",
        ),
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (!emailFromQuery) {
    return (
      <AuthFormLayout subtitle="Verify the one-time passcode sent to your email.">
        <FormAlert message="Email is missing. Please request a new OTP." />
        <p className={formStyles.footerLink}>
          <Link href={PATH_FORGOT_PASSWORD} className={formStyles.link}>
            Back to forgot password
          </Link>
        </p>
      </AuthFormLayout>
    );
  }

  return (
    <AuthFormLayout
      subtitle={`Enter the one-time passcode we sent to ${emailFromQuery}.`}
    >
      <Formik
        initialValues={otpInitialValues}
        validationSchema={otpSchema}
        onSubmit={handleSubmit}
      >
        {({ isSubmitting, status }) => (
          <Form className="mt-8 space-y-5" noValidate>
            <FormAlert message={status} />

            <FormTextField
              name="otp"
              id="otp"
              label="OTP"
              placeholder="Enter 8+ character code"
              autoComplete="one-time-code"
              icon={KeyRound}
              inputMode="text"
            />

            <CommonButton
              type="submit"
              loading={isSubmitting}
              disabled={isSubmitting}
              className={formStyles.submitButton}
              icon={<ArrowRight className="h-5 w-5" />}
              iconPosition="right"
            >
              Verify OTP
            </CommonButton>
          </Form>
        )}
      </Formik>

      <p className={formStyles.footerLink}>
        Didn&apos;t receive a code?{" "}
        <Link href={PATH_FORGOT_PASSWORD} className={formStyles.link}>
          Request again
        </Link>
        {" · "}
        <Link href={PATH_LOGIN} className={formStyles.link}>
          Log in
        </Link>
      </p>
    </AuthFormLayout>
  );
}

export default function OtpPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-1 items-center justify-center py-12 text-sm text-gray-500">
          Loading…
        </div>
      }
    >
      <OtpForm />
    </Suspense>
  );
}
