import * as React from "react";
import { Eye, EyeOff } from "lucide-react";

import { Input } from "@/components/ui/input";

export interface PasswordInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

export const PasswordInput = React.forwardRef<
  HTMLInputElement,
  PasswordInputProps
>(({ className = "", ...props }, ref) => {
  const [showPassword, setShowPassword] = React.useState(false);

  return (
    <div className="relative w-full">
      <Input
        ref={ref}
        type={showPassword ? "text" : "password"}
        className={`pr-12 ${className}`}
        {...props}
      />

      <button
        type="button"
        onClick={() => setShowPassword((prev) => !prev)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
        aria-label={showPassword ? "Hide password" : "Show password"}
      >
        {showPassword ? (
          <EyeOff className="h-5 w-5" />
        ) : (
          <Eye className="h-5 w-5" />
        )}
      </button>
    </div>
  );
});

PasswordInput.displayName = "PasswordInput";