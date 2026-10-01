import { Link } from "react-router-dom";

interface PlanUpgradeLinkProps {
  className?: string;
}

export default function PlanUpgradeLink({
  className = "mt-2 inline-block font-medium underline",
}: PlanUpgradeLinkProps) {
  return (
    <Link className={className} to="/dashboard/billing">
      View plans
    </Link>
  );
}
