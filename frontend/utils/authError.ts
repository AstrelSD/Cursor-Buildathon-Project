export function getAuthErrorMessage(
  err: unknown,
  fallback: string,
): string {
  if (
    err &&
    typeof err === "object" &&
    "message" in err &&
    typeof err.message === "string"
  ) {
    return err.message;
  }
  return fallback;
}
