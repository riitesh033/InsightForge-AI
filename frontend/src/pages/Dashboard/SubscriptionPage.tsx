import SubscriptionSettings from "@/components/settings/SubscriptionSettings";

export default function SubscriptionPage() {
  return (
    <div className="mx-auto min-w-0 max-w-5xl space-y-6">
      <header>
        <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
          Subscription
        </h2>
        <p className="mt-2 text-muted-foreground">
          View your current membership and available subscription actions.
        </p>
      </header>
      <SubscriptionSettings />
    </div>
  );
}
