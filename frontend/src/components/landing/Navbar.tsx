import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X, BarChart3 } from "lucide-react";

import ThemeToggle from "@/components/common/ThemeToggle";
import { Button } from "@/components/ui/button";
import Container from "@/components/ui/Container";

export default function Navbar() {
  const [open, setOpen] = useState(false);

  const closeMenu = () => setOpen(false);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <Container>
        <div className="flex h-20 items-center justify-between">

          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-3"
            onClick={closeMenu}
          >
            <div className="rounded-lg bg-indigo-600 p-2 text-white">
              <BarChart3 size={22} />
            </div>

            <div>
              <h1 className="text-lg font-bold text-foreground">
                InsightForge AI
              </h1>

              <p className="text-xs text-muted-foreground">
                Your AI Data Analyst
              </p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden items-center gap-8 md:flex">
            <a
              href="#features"
              className="text-muted-foreground transition hover:text-primary"
            >
              Features
            </a>

            <a
              href="#how-it-works"
              className="text-muted-foreground transition hover:text-primary"
            >
              How It Works
            </a>

            <a
              href="#pricing"
              className="text-muted-foreground transition hover:text-primary"
            >
              Pricing
            </a>

            <a
              href="#faq"
              className="text-muted-foreground transition hover:text-primary"
            >
              FAQ
            </a>
          </nav>

          {/* Desktop Right Side */}
          <div className="hidden items-center gap-3 md:flex">

            <ThemeToggle />

            <Link to="/login">
              <Button variant="ghost">
                Login
              </Button>
            </Link>

            <Link to="/register">
              <Button>
                Get Started
              </Button>
            </Link>

          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setOpen(!open)}
            className="md:hidden text-foreground"
          >
            {open ? <X size={24} /> : <Menu size={24} />}
          </button>

        </div>
      </Container>

      {/* Mobile Menu */}
      {open && (
        <div className="border-t border-border bg-background md:hidden">

          <div className="flex flex-col gap-5 p-6">

            <a href="#features" onClick={closeMenu}>
              Features
            </a>

            <a href="#how-it-works" onClick={closeMenu}>
              How It Works
            </a>

            <a href="#pricing" onClick={closeMenu}>
              Pricing
            </a>

            <a href="#faq" onClick={closeMenu}>
              FAQ
            </a>

            <div className="flex items-center justify-between border-t border-border pt-4">

              <span className="text-sm font-medium text-foreground">
                Theme
              </span>

              <ThemeToggle />

            </div>

            <Link to="/register" onClick={closeMenu}>
              <Button className="w-full">
                Get Started
              </Button>
            </Link>

            <Link to="/login" onClick={closeMenu}>
              <Button variant="outline" className="w-full">
                Login
              </Button>
            </Link>

          </div>

        </div>
      )}
    </header>
  );
}