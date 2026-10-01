import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";
import { getApiErrorMessage } from "@/lib/api";
import {
  createCheckout,
  getPlans,
  redirectToCheckout,
  type PaidPlan,
  type Plan,
} from "@/services/payments";
import PricingCard from "@/components/landing/PricingCard";

interface PlanCatalogProps {
  currentPlan?: Plan["plan_key"] | null;
  purchaseDisabled?: boolean;
}

function getPlanFeatures(plan: Plan): string[] {
  const limits = plan.limits;
  const limitFeatures: string[] = [];

  if (limits.max_datasets !== undefined) {
    limitFeatures.push(
      limits.max_datasets < 0
        ? "Unlimited datasets"
        : `Up to ${limits.max_datasets} datasets`
    );
  }
  if (limits.max_file_size_mb !== undefined) {
    limitFeatures.push(`Files up to ${limits.max_file_size_mb} MB`);
  }
  if (limits.ai_queries_per_month !== undefined) {
    limitFeatures.push(
      limits.ai_queries_per_month < 0
        ? "Unlimited AI queries"
        : `${limits.ai_queries_per_month} AI queries per month`
    );
  }

  return [...new Set([...plan.features, ...limitFeatures])];
}

export default function PlanCatalog({
  currentPlan = null,
  purchaseDisabled = false,
}: PlanCatalogProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [plansError, setPlansError] = useState<string | null>(null);
  const [checkoutPlan, setCheckoutPlan] = useState<PaidPlan | null>(null);

  const loadPlans = useCallback(async () => {
    setLoadingPlans(true);
    setPlansError(null);
    try {
      setPlans(await getPlans());
    } catch (error: unknown) {
      setPlansError(getApiErrorMessage(error, "Unable to load plans."));
    } finally {
      setLoadingPlans(false);
    }
  }, []);

  useEffect(() => {
    void loadPlans();
  }, [loadPlans]);

  async function selectPlan(plan: Plan) {
    if (plan.plan_key === currentPlan) return;

    if (plan.plan_key === "free") {
      navigate(isAuthenticated ? "/dashboard/subscription" : "/register");
      return;
    }

    if (!isAuthenticated) {
      navigate(`/login?plan=${plan.plan_key}`);
      return;
    }

    setCheckoutPlan(plan.plan_key);
    setPlansError(null);
    try {
      const checkoutUrl = await createCheckout(plan.plan_key);
      redirectToCheckout(checkoutUrl);
    } catch (error: unknown) {
      setPlansError(getApiErrorMessage(error, "Unable to start checkout."));
      setCheckoutPlan(null);
    }
  }

  if (loadingPlans) {
    return (
      <p role="status" className="py-8 text-center text-muted-foreground">
        Loading plans...
      </p>
    );
  }

  if (plansError && plans.length === 0) {
    return (
      <div role="alert" className="py-8 text-center">
        <p className="text-destructive">{plansError}</p>
        <button
          type="button"
          onClick={() => void loadPlans()}
          className="mt-4 rounded-lg bg-secondary px-4 py-2 text-sm font-medium text-secondary-foreground"
        >
          Retry
        </button>
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <p className="py-8 text-center text-muted-foreground">
        No pricing plans are currently available.
      </p>
    );
  }

  return (
    <>
      {plansError && (
        <div role="alert" className="mb-6 text-center">
          <p className="text-destructive">{plansError}</p>
          <button
            type="button"
            onClick={() => void loadPlans()}
            className="mt-2 rounded-lg bg-secondary px-4 py-2 text-sm font-medium text-secondary-foreground"
          >
            Retry
          </button>
        </div>
      )}
      <div className="grid min-w-0 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {plans.map((plan) => {
          const isCurrentPlan = plan.plan_key === currentPlan;
          return (
            <PricingCard
              key={plan.plan_key}
              title={plan.name}
              price={new Intl.NumberFormat(undefined, {
                style: "currency",
                currency: plan.currency,
                maximumFractionDigits: 0,
              }).format(plan.price)}
              features={getPlanFeatures(plan)}
              isFree={plan.plan_key === "free"}
              featured={plan.plan_key === "pro"}
              loading={checkoutPlan === plan.plan_key}
              disabled={
                checkoutPlan !== null ||
                purchaseDisabled ||
                isCurrentPlan
              }
              buttonLabel={isCurrentPlan ? "Current plan" : undefined}
              onSelect={() => void selectPlan(plan)}
            />
          );
        })}
      </div>
    </>
  );
}
