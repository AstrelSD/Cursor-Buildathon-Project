import { fetchUserLoans as fetchUserLoansFromApi } from "@/lib/api";
import type { LoanRow } from "@/lib/supabase";

export async function fetchUserLoans(userId: string): Promise<LoanRow[]> {
  return fetchUserLoansFromApi(userId);
}

export function subscribeUserLoans(
  userId: string,
  onChange: (loans: LoanRow[]) => void,
  onError?: (message: string) => void,
): () => void {
  async function refresh() {
    try {
      const loans = await fetchUserLoans(userId);
      onChange(loans);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Could not load your loans.";
      onError?.(message);
    }
  }

  void refresh();

  const poll = setInterval(() => {
    void refresh();
  }, 5000);

  return () => {
    clearInterval(poll);
  };
}
