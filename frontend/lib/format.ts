const lkrFormatter = new Intl.NumberFormat("en-LK", {
  style: "currency",
  currency: "LKR",
  maximumFractionDigits: 2,
});

export function formatLkr(amount: number): string {
  return lkrFormatter.format(amount);
}

export function formatBalanceDisplay(
  value: string | null | undefined,
  currency?: string | null,
): string {
  if (value == null || value === "—") return "—";
  const numeric = Number(String(value).replace(/,/g, ""));
  if (!Number.isFinite(numeric)) return value;
  const code = currency?.toUpperCase() === "LKR" || !currency ? "LKR" : currency;
  if (code === "LKR") return formatLkr(numeric);
  return `${numeric.toLocaleString("en-LK")} ${code}`;
}
