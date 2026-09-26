import api from "@/lib/api";

export type PaidPlan = "pro" | "business";
export type PlanKey = "free" | PaidPlan;

export interface Plan {
  plan_key: PlanKey;
  name: string;
  price: number;
  currency: string;
  features: string[];
  limits: {
    max_datasets: number;
    max_file_size_mb: number;
    ai_queries_per_month: number;
  };
}

export interface Subscription {
  plan: PlanKey;
  status: string;
  features: string[];
  limits: Plan["limits"];
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  started_at: string | null;
}

export interface PaymentRecord {
  id: number;
  amount: number;
  currency: string;
  status: string;
  plan_type: PlanKey;
  created_at: string;
  description: string | null;
}

export async function getPlans(): Promise<Plan[]> {
  const response = await api.get<{ plans: Plan[] }>("/payments/plans");
  return response.data.plans;
}

export async function createCheckout(planType: PaidPlan): Promise<string> {
  const response = await api.post<{ checkout_url: string }>(
    "/payments/create-checkout",
    null,
    { params: { plan_type: planType } }
  );
  return response.data.checkout_url;
}

export function redirectToCheckout(checkoutUrl: string): void {
  let checkout: URL;
  try {
    checkout = new URL(checkoutUrl);
  } catch {
    throw new Error("Stripe returned an invalid checkout URL.");
  }

  if (
    checkout.protocol !== "https:" ||
    checkout.hostname !== "checkout.stripe.com"
  ) {
    throw new Error("Stripe returned an untrusted checkout URL.");
  }

  window.location.assign(checkout.toString());
}

export async function getSubscription(): Promise<Subscription> {
  const response = await api.get<Subscription>("/payments/subscription");
  return response.data;
}

export async function cancelSubscription(): Promise<{ message: string }> {
  const response = await api.post<{ message: string }>("/payments/cancel");
  return response.data;
}

export async function getPaymentHistory(): Promise<{
  payments: PaymentRecord[];
  total: number;
}> {
  const response = await api.get<{ payments: PaymentRecord[]; total: number }>(
    "/payments/history"
  );
  return response.data;
}
