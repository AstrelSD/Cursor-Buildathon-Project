import styles from "@/app/styles/forms.module.css";

export { styles as formStyles };

export function fieldClass(
  error?: string,
  touched?: boolean,
  ...extras: (string | false | undefined)[]
): string {
  const invalid = touched && error;
  return [
    styles.input,
    invalid ? styles.inputError : styles.inputValid,
    ...extras,
  ]
    .filter(Boolean)
    .join(" ");
}
