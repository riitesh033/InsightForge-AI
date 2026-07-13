import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import Container from "@/components/ui/Container";
import { BarChart3 } from "lucide-react";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/80 backdrop-blur-lg">
      <Container>
        <div className="flex h-20 items-center justify-between">

          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-2"
          >
            <div className="rounded-lg bg-indigo-600 p-2 text-white">
              <BarChart3 size={22} />
            </div>

            <div>
              <h1 className="text-xl font-bold">
                InsightForge AI
              </h1>

              <p className="text-xs text-slate-500">
                Your AI Data Analyst
              </p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden items-center gap-8 md:flex">

            <a
              href="#features"
              className="text-slate-600 transition hover:text-indigo-600"
            >
              Features
            </a>

            <a
              href="#how-it-works"
              className="text-slate-600 transition hover:text-indigo-600"
            >
              How It Works
            </a>

            <a
              href="#pricing"
              className="text-slate-600 transition hover:text-indigo-600"
            >
              Pricing
            </a>

            <a
              href="#contact"
              className="text-slate-600 transition hover:text-indigo-600"
            >
              Contact
            </a>

          </nav>

          {/* Right Side */}
          <div className="hidden items-center gap-3 md:flex">

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

        </div>
      </Container>
    </header>
  );
}