import { useCallback, useEffect, useState } from "react";

import { getApiErrorMessage } from "@/lib/api";
import {
  cancelSubscription,
  getPaymentHistory,
  getSubscription,
  type PaymentRecord,
  type Subscription,
} from "@/services/payments";

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString() : "Not available";
}

function formatAmount(amount: number, currency: string): string {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
  }).format(amount);
}

export default function SubscriptionSettings() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelLoading, setCancelLoading] = useState(false);
  const [cancellationPending, setCancellationPending] = useState(false);
  const [cancelMessage, setCancelMessage] = useState<string | null>(null);

  const loadBilling = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [currentSubscription, history] = await Promise.all([
        getSubscription(),
        getPaymentHistory(),
      ]);
      setSubscription(currentSubscription);
      setPayments(history.payments);
      if (
        currentSubscription.cancel_at_period_end ||
        currentSubscription.status === "canceled"
      ) {
        setCancellationPending(false);
      }
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Unable to load billing details."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadBilling();
  }, [loadBilling]);

  async function requestCancellation() {
    setCancelLoading(true);
    setError(null);
    setCancelMessage(null);
    try {
      const result = await cancelSubscription();
      setCancellationPending(true);
      setCancelMessage(result.message);
      await loadBilling();
    } catch (cancelError) {
      setError(
        getApiErrorMessage(cancelError, "Unable to cancel this subscription.")
      );
    } finally {
      setCancelLoading(false);
    }
  }

  return (
    <section className="rounded-xl border border-border bg-card p-6">
      <h2 className="text-xl font-semibold text-foreground">Subscription</h2>

      {loading ? (
        <p role="status" className="mt-4 text-muted-foreground">
          Loading billing details...
        </p>
      ) : error ? (
        <div className="mt-4" role="alert">
          <p className="text-destructive">{error}</p>
          <button
            type="button"
            onClick={() => void loadBilling()}
            className="mt-3 rounded-lg bg-secondary px-4 py-2 text-sm font-medium"
          >
            Try again
          </button>
        </div>
      ) : subscription ? (
        <div className="mt-4 space-y-5">
          <div>
            <p className="text-foreground">
              <span className="font-semibold">{subscription.plan}</span>
              {" · "}
              <span className="capitalize">{subscription.status}</span>
            </p>
            {subscription.current_period_end && (
              <p className="mt-1 text-sm text-muted-foreground">
                Current period ends {formatDate(subscription.current_period_end)}.
              </p>
            )}
            {subscription.cancel_at_period_end && (
              <p className="mt-2 text-sm text-amber-600">
                Cancellation is confirmed for the end of this billing period.
              </p>
            )}
          </div>

          {cancelMessage && (
            <div role="status" className="text-sm text-muted-foreground">
              <p>{cancelMessage}</p>
              {cancellationPending && (
                <button
                  type="button"
                  onClick={() => void loadBilling()}
                  className="mt-2 rounded-lg bg-secondary px-3 py-1.5 font-medium"
                >
                  Refresh subscription status
                </button>
              )}
            </div>
          )}
          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}

          {subscription.plan !== "free" &&
            subscription.status !== "canceled" &&
            !subscription.cancel_at_period_end && (
              <button
                type="button"
                onClick={() => void requestCancellation()}
                disabled={cancelLoading || cancellationPending}
                className="rounded-lg border border-destructive px-4 py-2 text-sm font-medium text-destructive disabled:cursor-not-allowed disabled:opacity-60"
              >
                {cancelLoading
                  ? "Requesting cancellation..."
                  : cancellationPending
                    ? "Cancellation requested"
                    : "Cancel subscription"}
              </button>
            )}

          <div>
            <h3 className="font-semibold text-foreground">Payment history</h3>
            {payments.length === 0 ? (
              <p className="mt-2 text-sm text-muted-foreground">
                No payments have been recorded.
              </p>
            ) : (
              <ul className="mt-3 divide-y divide-border">
                {payments.map((payment) => (
                  <li
                    key={payment.id}
                    className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm"
                  >
                    <span className="text-foreground">
                      {payment.description ?? `${payment.plan_type} subscription`}
                    </span>
                    <span className="text-muted-foreground">
                      {formatAmount(payment.amount, payment.currency)} ·{" "}
                      <span className="capitalize">{payment.status}</span> ·{" "}
                      {formatDate(payment.created_at)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : null}
    </section>
  );
}
