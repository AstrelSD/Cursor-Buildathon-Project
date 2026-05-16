"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Formik, Form, type FormikHelpers } from "formik";
import { ArrowRight } from "lucide-react";
import { AuthFormLayout } from "@/components/auth/AuthFormLayout";
import { FormAlert, FormPasswordField } from "@/components/auth/form-fields";
import CommonButton from "@/components/ui/button";
import { PATH_LOGIN, PATH_OTP } from "@/constants/routes";
import type { ResetPasswordCredentials } from "@/types/user";
import { updatePassword } from "@/utils/authFunctions";
import { getAuthErrorMessage } from "@/utils/authError";
import { formStyles } from "@/utils/formFieldClass";
import {
  resetPasswordInitialValues,
  resetPasswordSchema,
} from "@/validation/resetPasswordSchema";

function getOtpBackHref() {
  if (typeof window === "undefined") return PATH_OTP;
  const email = sessionStorage.getItem("resetEmail");
  return email
    ? `${PATH_OTP}?email=${encodeURIComponent(email)}`
    : PATH_OTP;
}

export default function ResetPasswordPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleSubmit = async (
    values: ResetPasswordCredentials,
    { setSubmitting, setStatus }: FormikHelpers<ResetPasswordCredentials>,
  ) => {
    setStatus(undefined);
    try {
      await updatePassword(values.password);
      sessionStorage.removeItem("resetEmail");
      router.push(PATH_LOGIN);
    } catch (err: unknown) {
      setStatus(
        getAuthErrorMessage(
          err,
          "Could not reset password. Verify your OTP and try again.",
        ),
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthFormLayout subtitle="Choose a new password for your account.">
      <Formik
        initialValues={resetPasswordInitialValues}
        validationSchema={resetPasswordSchema}
        onSubmit={handleSubmit}
      >
        {({ isSubmitting, status }) => (
          <Form className="mt-8 space-y-5" noValidate>
            <FormAlert message={status} />

            <FormPasswordField
              name="password"
              id="password"
              label="New password"
              placeholder="Enter new password"
              show={showPassword}
              onToggle={() => setShowPassword((v) => !v)}
            />

            <FormPasswordField
              name="confirmPassword"
              id="confirmPassword"
              label="Confirm password"
              placeholder="Confirm new password"
              show={showConfirmPassword}
              onToggle={() => setShowConfirmPassword((v) => !v)}
            />

            <CommonButton
              type="submit"
              loading={isSubmitting}
              disabled={isSubmitting}
              className={formStyles.submitButton}
              icon={<ArrowRight className="h-5 w-5" />}
              iconPosition="right"
            >
              Reset Password
            </CommonButton>
          </Form>
        )}
      </Formik>

      <p className={formStyles.footerLink}>
        Need to verify OTP again?{" "}
        <Link href={getOtpBackHref()} className={formStyles.link}>
          Back to OTP
        </Link>
      </p>
    </AuthFormLayout>
  );
}
