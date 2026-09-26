import { Link } from "react-router-dom";

export default function PaymentCancelledPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6">
      <section className="max-w-lg text-center">
        <h1 className="text-3xl font-bold text-foreground">
          Checkout canceled
        </h1>
        <p className="mt-4 text-muted-foreground">
          No subscription was activated. You can return to pricing whenever
          you are ready.
        </p>
        <Link
          to="/#pricing"
          className="mt-8 inline-flex rounded-lg bg-primary px-6 py-3 font-semibold text-primary-foreground transition hover:opacity-90"
        >
          Return to pricing
        </Link>
      </section>
    </main>
  );
}
