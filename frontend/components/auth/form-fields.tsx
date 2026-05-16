"use client";

import { Field, type FieldProps } from "formik";
import type { LucideIcon } from "lucide-react";
import { Eye, EyeOff, Lock } from "lucide-react";
import { fieldClass, formStyles } from "@/utils/formFieldClass";

export function FormAlert({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p className={formStyles.formAlert} role="alert">
      {message}
    </p>
  );
}

export function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p className={formStyles.fieldError} role="alert">
      {message}
    </p>
  );
}

type FormTextFieldProps = {
  name: string;
  id: string;
  label: string;
  type?: string;
  placeholder: string;
  autoComplete?: string;
  icon: LucideIcon;
  readOnly?: boolean;
  inputMode?: React.HTMLAttributes<HTMLInputElement>["inputMode"];
};

export function FormTextField({
  name,
  id,
  label,
  type = "text",
  placeholder,
  autoComplete,
  icon: Icon,
  readOnly,
  inputMode,
}: FormTextFieldProps) {
  return (
    <div>
      <label htmlFor={id} className={formStyles.label}>
        {label}
      </label>
      <Field name={name}>
        {({ field, meta }: FieldProps<string>) => (
          <>
            <div className="relative">
              <Icon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input
                {...field}
                id={id}
                type={type}
                placeholder={placeholder}
                autoComplete={autoComplete}
                readOnly={readOnly}
                inputMode={inputMode}
                className={fieldClass(
                  meta.error,
                  meta.touched,
                  formStyles.iconLeft,
                  readOnly && formStyles.inputReadonly,
                )}
              />
            </div>
            <FieldError message={meta.touched ? meta.error : undefined} />
          </>
        )}
      </Field>
    </div>
  );
}

type FormTextAreaFieldProps = {
  name: string;
  id: string;
  label: string;
  placeholder: string;
  icon: LucideIcon;
  rows?: number;
};

export function FormTextAreaField({
  name,
  id,
  label,
  placeholder,
  icon: Icon,
  rows = 3,
}: FormTextAreaFieldProps) {
  return (
    <div>
      <label htmlFor={id} className={formStyles.label}>
        {label}
      </label>
      <Field name={name}>
        {({ field, meta }: FieldProps<string>) => (
          <>
            <div className="relative">
              <Icon className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <textarea
                {...field}
                id={id}
                rows={rows}
                placeholder={placeholder}
                autoComplete="street-address"
                className={fieldClass(
                  meta.error,
                  meta.touched,
                  formStyles.iconLeft,
                  formStyles.textarea,
                )}
              />
            </div>
            <FieldError message={meta.touched ? meta.error : undefined} />
          </>
        )}
      </Field>
    </div>
  );
}

type FormPasswordFieldProps = {
  name: string;
  id: string;
  label: string;
  placeholder: string;
  show: boolean;
  onToggle: () => void;
  autoComplete?: string;
};

export function FormPasswordField({
  name,
  id,
  label,
  placeholder,
  show,
  onToggle,
  autoComplete = "new-password",
}: FormPasswordFieldProps) {
  return (
    <div>
      <label htmlFor={id} className={formStyles.label}>
        {label}
      </label>
      <Field name={name}>
        {({ field, meta }: FieldProps<string>) => (
          <>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input
                {...field}
                id={id}
                type={show ? "text" : "password"}
                placeholder={placeholder}
                autoComplete={autoComplete}
                className={fieldClass(
                  meta.error,
                  meta.touched,
                  formStyles.iconRight,
                )}
              />
              <button
                type="button"
                onClick={onToggle}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label={show ? "Hide password" : "Show password"}
              >
                {show ? (
                  <EyeOff className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
                )}
              </button>
            </div>
            <FieldError message={meta.touched ? meta.error : undefined} />
          </>
        )}
      </Field>
    </div>
  );
}
