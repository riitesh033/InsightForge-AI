import { useCallback, useEffect, useState } from "react";

import PlanCatalog from "@/components/payments/PlanCatalog";
import { getApiErrorMessage } from "@/lib/api";
import { getSubscription, type Subscription } from "@/services/payments";

export default function BillingPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [subscriptionError, setSubscriptionError] = useState<string | null>(
    null
  );
  const [loadingSubscription, setLoadingSubscription] = useState(true);

  const loadSubscription = useCallback(async () => {
    setLoadingSubscription(true);
    setSubscriptionError(null);
    try {
      setSubscription(await getSubscription());
    } catch (error: unknown) {
      setSubscriptionError(
        getApiErrorMessage(error, "Unable to load your current plan.")
      );
    } finally {
      setLoadingSubscription(false);
    }
  }, []);

  useEffect(() => {
    void loadSubscription();
  }, [loadSubscription]);

  return (
    <div className="mx-auto min-w-0 max-w-7xl space-y-8">
      <header>
        <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
          Plan &amp; Billing
        </h2>
        <p className="mt-2 text-muted-foreground">
          Choose or change your membership using the available plans.
        </p>
      </header>

      {loadingSubscription ? (
        <p role="status" className="text-muted-foreground">
          Checking your current plan...
        </p>
      ) : subscriptionError ? (
        <div role="alert" className="rounded-xl border border-border bg-card p-4">
          <p className="text-destructive">{subscriptionError}</p>
          <button
            type="button"
            onClick={() => void loadSubscription()}
            className="mt-3 rounded-lg bg-secondary px-4 py-2 text-sm font-medium text-secondary-foreground"
          >
            Retry
          </button>
        </div>
      ) : subscription ? (
        <p className="text-sm text-muted-foreground">
          Current plan:{" "}
          <span className="font-semibold capitalize text-foreground">
            {subscription.plan}
          </span>
        </p>
      ) : null}

      <PlanCatalog
        currentPlan={subscription?.plan}
        purchaseDisabled={loadingSubscription || subscriptionError !== null}
      />
    </div>
  );
}
