import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
  size?: number;
}

export default function LoadingSpinner({
  size = 24,
}: LoadingSpinnerProps) {
  return (
    <Loader2
      size={size}
      className="animate-spin text-primary"
    />
  );
}