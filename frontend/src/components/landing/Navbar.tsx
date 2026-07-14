import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X, BarChart3 } from "lucide-react";

import ThemeToggle from "@/components/common/ThemeToggle";
import { Button } from "@/components/ui/button";
import Container from "@/components/ui/Container";

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90">
      <Container>
        <div className="flex h-20 items-center justify-between">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="rounded-lg bg-indigo-600 p-2 text-white">
              <BarChart3 size={22} />
            </div>

            <div>
              <h1 className="text-lg font-bold dark:text-white">
                InsightForge AI
              </h1>

              <p className="text-xs text-slate-500 dark:text-slate-400">
                Your AI Data Analyst
              </p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden items-center gap-8 md:flex">
            <a
              href="#features"
              className="text-slate-600 transition hover:text-indigo-600 dark:text-slate-300"
            >
              Features
            </a>

            <a
              href="#how-it-works"
              className="text-slate-600 transition hover:text-indigo-600 dark:text-slate-300"
            >
              How It Works
            </a>

            <a
              href="#pricing"
              className="text-slate-600 transition hover:text-indigo-600 dark:text-slate-300"
            >
              Pricing
            </a>

            <a
              href="#faq"
              className="text-slate-600 transition hover:text-indigo-600 dark:text-slate-300"
            >
              FAQ
            </a>
          </nav>

          {/* Desktop Right Side */}
          <div className="hidden items-center gap-3 md:flex">

            <ThemeToggle />

            <Button variant="ghost">
              Login
            </Button>

            <Button>
              Get Started
            </Button>

          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setOpen(!open)}
            className="text-slate-700 dark:text-white md:hidden"
          >
            {open ? <X size={24} /> : <Menu size={24} />}
          </button>

        </div>
      </Container>

      {/* Mobile Menu */}
      {open && (
        <div className="border-t border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950 md:hidden">

          <div className="flex flex-col gap-5 p-6">

            <a
              href="#features"
              onClick={() => setOpen(false)}
            >
              Features
            </a>

            <a
              href="#how-it-works"
              onClick={() => setOpen(false)}
            >
              How It Works
            </a>

            <a
              href="#pricing"
              onClick={() => setOpen(false)}
            >
              Pricing
            </a>

            <a
              href="#faq"
              onClick={() => setOpen(false)}
            >
              FAQ
            </a>

            <div className="flex items-center justify-between border-t border-slate-200 pt-4 dark:border-slate-800">
              <span className="text-sm font-medium dark:text-white">
                Theme
              </span>

              <ThemeToggle />
            </div>

            <Button className="w-full">
              Get Started
            </Button>

          </div>

        </div>
      )}
    </header>
  );
}