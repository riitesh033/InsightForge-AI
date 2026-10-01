import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import api from "@/lib/api";

type PaymentResult =
  | { status: "loading" }
  | { status: "pending" }
  | { status: "success"; plan: string; message: string }
  | { status: "failed" }
  | { status: "error" };

interface CheckoutStatusResponse {
  status: "pending" | "success" | "failed";
  success: boolean;
  plan?: string;
  message?: string;
}

const WEBHOOK_POLL_INTERVAL_MS = 1500;
const MAX_WEBHOOK_POLLS = 12;

export default function PaymentSuccessPage() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const [result, setResult] = useState<PaymentResult>({ status: "loading" });

  useEffect(() => {
    let active = true;
    let timeoutId: number | undefined;

    if (!sessionId) {
      setResult({ status: "error" });
      return;
    }

    async function checkStatus(attempt: number): Promise<void> {
      try {
        const { data } = await api.get<CheckoutStatusResponse>(
          "/payments/success",
          { params: { session_id: sessionId } }
        );
        if (!active) return;

        if (data.status === "success" && data.plan) {
          setResult({
            status: "success",
            plan: data.plan,
            message: data.message ?? "Subscription confirmed.",
          });
          return;
        }
        if (data.status === "failed") {
          setResult({ status: "failed" });
          return;
        }
        if (attempt >= MAX_WEBHOOK_POLLS) {
          setResult({ status: "pending" });
          return;
        }

        timeoutId = window.setTimeout(
          () => void checkStatus(attempt + 1),
          WEBHOOK_POLL_INTERVAL_MS
        );
      } catch {
        if (active) setResult({ status: "error" });
      }
    }

    void checkStatus(1);
    return () => {
      active = false;
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
    };
  }, [sessionId]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6">
      <section className="max-w-lg text-center">
        {result.status === "loading" ? (
          <>
            <h1 className="text-3xl font-bold text-foreground">
              Confirming payment
            </h1>
            <p role="status" className="mt-4 text-muted-foreground">
              Waiting for Stripe to confirm your subscription.
            </p>
          </>
        ) : result.status === "success" ? (
          <>
            <h1 className="text-3xl font-bold text-foreground">
              Payment successful
            </h1>
            <p className="mt-4 text-muted-foreground">
              {result.message} Your {result.plan} plan is ready.
            </p>
          </>
        ) : result.status === "pending" ? (
          <>
            <h1 className="text-3xl font-bold text-foreground">
              Payment received
            </h1>
            <p role="status" className="mt-4 text-muted-foreground">
              Stripe has not confirmed the subscription yet. Check your
              subscription settings again shortly; this page has not activated
              the plan.
            </p>
          </>
        ) : (
          <>
            <h1 className="text-3xl font-bold text-foreground">
              {result.status === "failed"
                ? "Checkout was not completed"
                : "Payment could not be confirmed"}
            </h1>
            <p role="alert" className="mt-4 text-muted-foreground">
              Check your subscription status or contact support if you were
              charged.
            </p>
          </>
        )}
        <Link
          to="/dashboard/subscription"
          className="mt-8 inline-flex rounded-lg bg-primary px-6 py-3 font-semibold text-primary-foreground transition hover:opacity-90"
        >
          View subscription
        </Link>
      </section>
    </main>
  );
}
