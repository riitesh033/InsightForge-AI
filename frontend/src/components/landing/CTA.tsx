import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

export default function CTA() {
  return (
    <section className="bg-white py-28 transition-colors duration-300 dark:bg-slate-900">
      <div className="mx-auto max-w-5xl px-6">

        <div className="rounded-3xl bg-indigo-600 p-16 text-center text-white shadow-2xl">

          <h2 className="text-4xl font-bold">
            Ready to Transform Your Data?
          </h2>

          <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-indigo-100">
            Upload your datasets, generate AI insights,
            detect anomalies, build dashboards,
            and export professional reports in minutes.
          </p>

          <div className="mt-10 flex flex-col justify-center gap-4 sm:flex-row">

            <Link to="/register">
              <Button
                size="lg"
                className="bg-white text-indigo-600 hover:bg-slate-100"
              >
                Get Started
              </Button>
            </Link>

            <Button
              size="lg"
              variant="outline"
              className="
                border-white
                bg-transparent
                text-white
                hover:bg-white
                hover:text-indigo-600
              "
            >
              Live Demo
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>

          </div>

        </div>

      </div>
    </section>
  );
}