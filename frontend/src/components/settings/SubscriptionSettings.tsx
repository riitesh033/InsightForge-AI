import { useCallback, useEffect, useState } from "react";

import { getApiErrorMessage } from "@/lib/api";
import {
  cancelSubscription,
  getSubscription,
  type Subscription,
} from "@/services/payments";

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString() : "Not available";
}

export default function SubscriptionSettings() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelLoading, setCancelLoading] = useState(false);
  const [cancellationPending, setCancellationPending] = useState(false);
  const [cancelMessage, setCancelMessage] = useState<string | null>(null);

  const loadBilling = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const currentSubscription = await getSubscription();
      setSubscription(currentSubscription);
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
    <section
      className="rounded-xl border border-border bg-card p-4 sm:p-6"
    >
      <h2 className="text-xl font-semibold text-foreground">Current plan</h2>

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
          <dl className="grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm text-muted-foreground">Plan</dt>
              <dd className="mt-1 font-semibold capitalize text-foreground">
                {subscription.plan}
                {subscription.plan === "free" && " (Free)"}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-muted-foreground">Status</dt>
              <dd className="mt-1 font-semibold capitalize text-foreground">
                {subscription.status}
              </dd>
            </div>
            {subscription.started_at && (
              <div>
                <dt className="text-sm text-muted-foreground">
                  Subscription started
                </dt>
                <dd className="mt-1 text-foreground">
                  {formatDate(subscription.started_at)}
                </dd>
              </div>
            )}
            {subscription.current_period_start && (
              <div>
                <dt className="text-sm text-muted-foreground">
                  Current period started
                </dt>
                <dd className="mt-1 text-foreground">
                  {formatDate(subscription.current_period_start)}
                </dd>
              </div>
            )}
            {subscription.current_period_end && (
              <div>
                <dt className="text-sm text-muted-foreground">
                  {subscription.cancel_at_period_end
                    ? "Subscription ends"
                    : "Current period ends"}
                </dt>
                <dd className="mt-1 text-foreground">
                  {formatDate(subscription.current_period_end)}
                </dd>
              </div>
            )}
          </dl>
          {subscription.cancel_at_period_end && (
            <p className="text-sm text-amber-600">
              Cancellation is confirmed for the end of this billing period.
            </p>
          )}

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

        </div>
      ) : null}
    </section>
  );
}
