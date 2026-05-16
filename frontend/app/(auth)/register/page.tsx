"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Formik, Form, type FormikHelpers } from "formik";
import { ArrowRight, Mail, MapPin, Phone, User } from "lucide-react";
import { AuthFormLayout } from "@/components/auth/AuthFormLayout";
import { useAuth } from "@/components/providers/AuthProvider";
import { useToast } from "@/hooks/useToast";
import {
  FormAlert,
  FormPasswordField,
  FormSelectField,
  FormTextAreaField,
  FormTextField,
} from "@/components/auth/form-fields";
import CommonButton from "@/components/ui/button";
import { PATH_APPLY, PATH_LOGIN } from "@/constants/routes";
import type { RegisterCredentials } from "@/types/user";
import { signUpWithEmail } from "@/utils/authFunctions";
import { getAuthErrorMessage } from "@/utils/authError";
import { formStyles } from "@/utils/formFieldClass";
import { SRI_LANKA_DISTRICTS } from "@/constants/districts";
import {
  registerInitialValues,
  registerSchema,
} from "@/validation/registerSchema";

export default function RegisterPage() {
  const router = useRouter();
  const { refreshSession } = useAuth();
  const { success: toastSuccess } = useToast();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleSubmit = async (
    values: RegisterCredentials,
    { setSubmitting, setStatus }: FormikHelpers<RegisterCredentials>,
  ) => {
    setStatus(undefined);
    try {
      await signUpWithEmail(values.email, values.password, {
        firstName: values.firstName,
        lastName: values.lastName,
        phone: values.phone,
        district: values.district,
        address: values.address,
      });
      await refreshSession();
      toastSuccess("Your account has been registered successfully.");
      router.push(PATH_APPLY);
      router.refresh();
    } catch (err: unknown) {
      setStatus(getAuthErrorMessage(err, "Registration failed"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthFormLayout
      subtitle="Create your Agri-Lend account"
      maxWidth="lg"
    >
      <Formik
        initialValues={registerInitialValues}
        validationSchema={registerSchema}
        onSubmit={handleSubmit}
      >
        {({ isSubmitting, status }) => (
          <Form className="mt-8 space-y-5" noValidate>
            <FormAlert message={status} />

            <div className="grid gap-4 sm:grid-cols-2">
              <FormTextField
                name="firstName"
                id="firstName"
                label="First name"
                placeholder="First name"
                autoComplete="given-name"
                icon={User}
              />
              <FormTextField
                name="lastName"
                id="lastName"
                label="Last name"
                placeholder="Last name"
                autoComplete="family-name"
                icon={User}
              />
            </div>

            <FormTextField
              name="email"
              id="email"
              label="Email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              icon={Mail}
            />

            <FormTextField
              name="phone"
              id="phone"
              label="Phone number"
              type="tel"
              placeholder="+94771234567"
              autoComplete="tel"
              icon={Phone}
            />

            <FormSelectField
              name="district"
              id="district"
              label="Farm district"
              options={SRI_LANKA_DISTRICTS}
              icon={MapPin}
            />

            <FormTextAreaField
              name="address"
              id="address"
              label="Address"
              placeholder="Farm or mailing address"
              icon={MapPin}
            />

            <FormPasswordField
              name="password"
              id="password"
              label="Password"
              placeholder="Create a password"
              show={showPassword}
              onToggle={() => setShowPassword((v) => !v)}
            />

            <FormPasswordField
              name="confirmPassword"
              id="confirmPassword"
              label="Confirm password"
              placeholder="Confirm your password"
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
              Register
            </CommonButton>
          </Form>
        )}
      </Formik>

      <p className={formStyles.footerLink}>
        Already have an account?{" "}
        <Link href={PATH_LOGIN} className={formStyles.link}>
          Log in
        </Link>
      </p>
    </AuthFormLayout>
  );
}
