"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import {
  FARMER_PAYOUT_ACCOUNT,
  FARMER_PAYOUT_BANK_CODE,
} from "@/constants/banking";
import { fetchPayoutAccountBalance } from "@/lib/api";
import { formatBalanceDisplay } from "@/lib/format";
import { fetchProfilePayout, updateProfilePayout } from "@/lib/profile";

type PayoutAccountFormProps = {
  userId: string;
};

export function PayoutAccountForm({ userId }: PayoutAccountFormProps) {
  const [account, setAccount] = useState(FARMER_PAYOUT_ACCOUNT);
  const [bankCode, setBankCode] = useState(FARMER_PAYOUT_BANK_CODE);
  const [balanceLabel, setBalanceLabel] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const profile = await fetchProfilePayout(userId);
        if (cancelled) return;
        if (profile.payout_account_number) setAccount(profile.payout_account_number);
        if (profile.payout_bank_code) setBankCode(profile.payout_bank_code);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not load payout settings from server.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  useEffect(() => {
    void fetchPayoutAccountBalance()
      .then((b) => {
        setBalanceLabel(
          formatBalanceDisplay(b.available_balance, b.currency),
        );
      })
      .catch(() => {
        setBalanceLabel(null);
      });
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await updateProfilePayout(userId, {
        payout_account_number: account.trim(),
        payout_bank_code: bankCode.trim(),
      });
      setMessage("Payout account saved. CEFTS repayments use these details.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-xl border border-gray-100 bg-white p-5 text-sm text-gray-500">
        <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
        Loading payout settings…
      </div>
    );
  }

  return (
    <form
      onSubmit={(e) => void handleSave(e)}
      className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm"
    >
      <h2 className="font-semibold text-gray-900">Payout bank account</h2>
      <p className="mt-1 text-sm text-gray-600">
        Stored on your profile for disbursements and CEFTS repayments. Sandbox balance
        below always uses test account {FARMER_PAYOUT_ACCOUNT}.
      </p>
      {balanceLabel ? (
        <p className="mt-2 text-sm font-medium text-[#2E7D32]">
          Sandbox test balance: {balanceLabel}
        </p>
      ) : null}
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="payout-account" className="mb-1 block text-sm font-medium text-gray-700">
            Account number
          </label>
          <input
            id="payout-account"
            value={account}
            onChange={(e) => setAccount(e.target.value)}
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="payout-bank" className="mb-1 block text-sm font-medium text-gray-700">
            Bank code
          </label>
          <input
            id="payout-bank"
            value={bankCode}
            onChange={(e) => setBankCode(e.target.value)}
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm"
          />
        </div>
      </div>
      {error ? <p className="mt-2 text-sm text-red-700">{error}</p> : null}
      {message ? <p className="mt-2 text-sm text-emerald-800">{message}</p> : null}
      <button
        type="submit"
        disabled={saving}
        className="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
      >
        {saving ? "Saving…" : "Save account"}
      </button>
    </form>
  );
}
