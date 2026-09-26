import { useEffect, useState } from "react";
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
import PricingCard from "./PricingCard";

export default function Pricing() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [plansError, setPlansError] = useState<string | null>(null);
  const [checkoutPlan, setCheckoutPlan] = useState<PaidPlan | null>(null);

  useEffect(() => {
    let active = true;
    getPlans()
      .then((availablePlans) => {
        if (active) setPlans(availablePlans);
      })
      .catch((error: unknown) => {
        if (active) {
          setPlansError(getApiErrorMessage(error, "Unable to load plans."));
        }
      })
      .finally(() => {
        if (active) setLoadingPlans(false);
      });

    return () => {
      active = false;
    };
  }, []);

  async function selectPlan(plan: Plan) {
    if (plan.plan_key === "free") {
      navigate(isAuthenticated ? "/dashboard/settings" : "/register");
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
    } catch (error) {
      setPlansError(getApiErrorMessage(error, "Unable to start checkout."));
      setCheckoutPlan(null);
    }
  }

  return (
    <section id="pricing" className="bg-slate-50 py-28 dark:bg-slate-900">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mb-16 text-center">
          <span className="inline-block rounded-full bg-indigo-100 px-4 py-2 text-sm font-semibold text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
            Pricing
          </span>
          <h2 className="mt-6 text-4xl font-bold text-slate-900 dark:text-white">
            Simple Pricing
          </h2>
          <p className="mt-4 text-lg text-slate-600 dark:text-slate-400">
            Choose the plan that fits your needs.
          </p>
        </div>

        {loadingPlans ? (
          <p role="status" className="text-center text-muted-foreground">
            Loading plans...
          </p>
        ) : plansError && plans.length === 0 ? (
          <p role="alert" className="text-center text-destructive">
            {plansError}
          </p>
        ) : (
          <>
            {plansError && (
              <p role="alert" className="mb-6 text-center text-destructive">
                {plansError}
              </p>
            )}
            <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {plans.map((plan) => (
                <PricingCard
                  key={plan.plan_key}
                  title={plan.name}
                  price={new Intl.NumberFormat(undefined, {
                    style: "currency",
                    currency: plan.currency,
                    maximumFractionDigits: 0,
                  }).format(plan.price)}
                  features={plan.features}
                  isFree={plan.plan_key === "free"}
                  featured={plan.plan_key === "pro"}
                  loading={checkoutPlan === plan.plan_key}
                  disabled={checkoutPlan !== null}
                  onSelect={() => void selectPlan(plan)}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}
