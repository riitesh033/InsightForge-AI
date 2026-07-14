import { Link } from "react-router-dom";
import { BarChart3 } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
      <div className="mx-auto max-w-7xl px-6 py-14">

        <div className="grid gap-10 md:grid-cols-4">

          {/* Brand */}

          <div>

            <div className="flex items-center gap-2">

              <div className="rounded-lg bg-indigo-600 p-2 text-white">

                <BarChart3 size={20} />

              </div>

              <div>

                <h3 className="font-bold">

                  InsightForge AI

                </h3>

                <p className="text-xs text-slate-500">

                  Your AI Data Analyst

                </p>

              </div>

            </div>

            <p className="mt-5 text-sm leading-7 text-slate-600">
              AI-powered dataset analysis platform built using
              React, FastAPI, PostgreSQL and Machine Learning.
            </p>

          </div>

          {/* Product */}

          <div>

            <h4 className="mb-4 font-semibold">
              Product
            </h4>

            <ul className="space-y-3 text-slate-600">

              <li><a href="#features">Features</a></li>

              <li><a href="#pricing">Pricing</a></li>

              <li><a href="#faq">FAQ</a></li>

            </ul>

          </div>

          {/* Company */}

          <div>

            <h4 className="mb-4 font-semibold">
              Company
            </h4>

            <ul className="space-y-3 text-slate-600">

              <li>
                <Link to="/about">
                  About
                </Link>
              </li>

              <li>
                <Link to="/contact">
                  Contact
                </Link>
              </li>

            </ul>

          </div>

          {/* Resources */}

          <div>

            <h4 className="mb-4 font-semibold">
              Resources
            </h4>

            <ul className="space-y-3 text-slate-600">

              <li>Documentation</li>

              <li>GitHub</li>

              <li>Privacy Policy</li>

            </ul>

          </div>

        </div>

        <div className="mt-12 border-t border-slate-200 pt-6 text-center text-sm text-slate-500">

          © 2026 InsightForge AI. All rights reserved.

        </div>

      </div>
    </footer>
  );
}