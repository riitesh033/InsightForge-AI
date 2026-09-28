import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";

export default function GoogleCallbackPage() {
  const { completeGoogleLogin } = useAuth();
  const navigate = useNavigate();
  const handled = useRef(false);

  useEffect(() => {
    if (handled.current) return;
    handled.current = true;

    const fragment = new URLSearchParams(window.location.hash.slice(1));
    const accessToken = fragment.get("access_token");
    window.history.replaceState(null, "", window.location.pathname);

    if (!accessToken) {
      navigate("/login?google_error=invalid_response", { replace: true });
      return;
    }

    void completeGoogleLogin(accessToken)
      .then(() => navigate("/dashboard", { replace: true }))
      .catch(() => navigate("/login?google_error=invalid_response", { replace: true }));
  }, [completeGoogleLogin, navigate]);

  return (
    <div className="mx-auto w-full max-w-md rounded-2xl border border-border bg-card p-8 text-center shadow-xl">
      <p className="text-foreground">Completing Google sign-in...</p>
    </div>
  );
}
