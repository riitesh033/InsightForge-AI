import { Button } from "@/components/ui/button";
import Container from "@/components/ui/Container";
import { ArrowRight, Sparkles } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative overflow-hidden py-28">

      <Container>

        <div className="grid items-center gap-20 lg:grid-cols-2">

          {/* Left */}

          <div>

            <div className="inline-flex items-center gap-2 rounded-full bg-indigo-100 px-4 py-2 text-sm font-medium text-indigo-700">

              <Sparkles size={16} />

              AI Powered Data Analytics

            </div>

            <h1 className="mt-8 text-5xl font-extrabold leading-tight lg:text-7xl">

              Transform

              <span className="text-indigo-600">

                {" "}Raw Data

              </span>

              <br />

              Into Insights

            </h1>

            <p className="mt-8 max-w-xl text-lg leading-8 text-slate-600">

              Upload CSV or Excel files, let AI clean your data,
              generate charts, detect anomalies,
              and create professional reports automatically.

            </p>

            <div className="mt-10 flex gap-4">

              <Button size="lg">

                Get Started

              </Button>

              <Button variant="outline" size="lg">

                Live Demo

                <ArrowRight className="ml-2 h-4 w-4" />

              </Button>

            </div>

          </div>

          {/* Right */}

          <div>

            <div className="rounded-3xl bg-gradient-to-br from-indigo-600 via-violet-500 to-blue-500 p-10 text-white shadow-2xl">

              <h2 className="text-3xl font-bold">

                AI Dashboard

              </h2>

              <div className="mt-8 space-y-4">

                <div className="rounded-xl bg-white/20 p-4">

                  Dataset Health Score

                  <h3 className="text-4xl font-bold">

                    97%

                  </h3>

                </div>

                <div className="rounded-xl bg-white/20 p-4">

                  Missing Values Fixed

                  <h3 className="text-4xl font-bold">

                    254

                  </h3>

                </div>

                <div className="rounded-xl bg-white/20 p-4">

                  AI Insights Generated

                  <h3 className="text-4xl font-bold">

                    43

                  </h3>

                </div>

              </div>

            </div>

          </div>

        </div>

      </Container>

    </section>
  );
}