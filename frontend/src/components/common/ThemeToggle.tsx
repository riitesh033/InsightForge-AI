import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useTheme } from "@/context/ThemeContext";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className="
        shrink-0
        text-foreground
        hover:bg-accent
        hover:text-accent-foreground
        transition-colors
        duration-200
      "
      aria-label={
        theme === "light" ? "Enable dark mode" : "Enable light mode"
      }
      title={theme === "light" ? "Dark mode" : "Light mode"}
    >
      {theme === "light" ? (
        <Moon className="h-5 w-5" aria-hidden="true" />
      ) : (
        <Sun className="h-5 w-5 text-yellow-500" aria-hidden="true" />
      )}
    </Button>
  );
}