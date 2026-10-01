import { useCallback, useEffect, useState } from "react";

import { getApiErrorMessage } from "@/lib/api";
import {
  getPaymentHistory,
  type PaymentRecord,
} from "@/services/payments";

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Not available"
    : date.toLocaleDateString();
}

function formatAmount(amount: number, currency: string): string {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
  }).format(amount);
}

export default function PaymentHistoryPage() {
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPayments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getPaymentHistory();
      setPayments(result.payments);
    } catch (loadError: unknown) {
      setError(
        getApiErrorMessage(loadError, "Unable to load payment history.")
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPayments();
  }, [loadPayments]);

  return (
    <div className="mx-auto min-w-0 max-w-5xl space-y-6">
      <header>
        <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
          Payment History
        </h2>
        <p className="mt-2 text-muted-foreground">
          Review payments recorded for your account.
        </p>
      </header>

      <section
        aria-label="Payment history"
        className="rounded-xl border border-border bg-card p-4 sm:p-6"
      >
        {loading ? (
          <p role="status" className="py-4 text-muted-foreground">
            Loading payment history...
          </p>
        ) : error ? (
          <div role="alert">
            <p className="text-destructive">{error}</p>
            <button
              type="button"
              onClick={() => void loadPayments()}
              className="mt-3 rounded-lg bg-secondary px-4 py-2 text-sm font-medium text-secondary-foreground"
            >
              Retry
            </button>
          </div>
        ) : payments.length === 0 ? (
          <p className="rounded-lg bg-muted/50 px-4 py-6 text-center text-muted-foreground">
            No payments have been recorded.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {payments.map((payment) => (
              <li
                key={payment.id}
                className="grid min-w-0 gap-2 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
              >
                <div className="min-w-0">
                  <p className="break-words font-medium text-foreground">
                    {payment.description ??
                      `${payment.plan_type} subscription`}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {formatDate(payment.created_at)}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm sm:justify-end">
                  <span className="font-medium text-foreground">
                    {formatAmount(payment.amount, payment.currency)}
                  </span>
                  <span className="capitalize text-muted-foreground">
                    {payment.status}
                  </span>
                  <span className="capitalize text-muted-foreground">
                    {payment.plan_type}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
