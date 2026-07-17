import { Link } from "react-router-dom";
import { ArrowRight, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import Container from "@/components/ui/Container";

export default function Hero() {
  return (
    <section className="relative bg-transparent py-28">
      <Container>
        <div className="grid items-center gap-20 lg:grid-cols-2">

          {/* Left */}
          <div>

            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
              <Sparkles className="h-4 w-4" />
              AI Powered Data Analytics
            </div>

            <h1 className="mt-8 text-5xl font-extrabold leading-tight text-foreground lg:text-7xl">
              Transform
              <span className="text-primary">
                {" "}Raw Data
              </span>
              <br />
              Into Insights
            </h1>

            <p className="mt-8 max-w-xl text-lg leading-8 text-muted-foreground">
              Upload CSV or Excel datasets, let AI clean your data,
              detect anomalies, generate interactive visualizations,
              and produce professional reports within seconds.
            </p>

            <div className="mt-10 flex flex-wrap gap-4">

              <Link to="/register">
                <Button size="lg">
                  Get Started
                </Button>
             </Link>

               <Link to="/demo">
               <Button
                 variant="outline"
                  size="lg"
                 className="
                 border-border
                 bg-transparent
                 text-foreground
                 hover:bg-accent
                 hover:text-accent-foreground
                 "
               >
                 Live Demo
                  <ArrowRight className="ml-2 h-4 w-4" />
               </Button>
              </Link>

            </div>

          </div>

          {/* Right */}
          <div>

            <div className="rounded-3xl border border-border bg-card p-10 shadow-2xl backdrop-blur">

              <h2 className="text-3xl font-bold text-foreground">
                AI Dashboard
              </h2>

              <div className="mt-8 space-y-4">

                <div className="rounded-xl bg-primary p-4 text-primary-foreground">
                  Dataset Health Score

                  <h3 className="text-4xl font-bold">
                    97%
                  </h3>
                </div>

                <div className="rounded-xl border border-border bg-background p-4">

                  <p className="text-muted-foreground">
                    Missing Values Fixed
                  </p>

                  <h3 className="text-4xl font-bold text-foreground">
                    254
                  </h3>

                </div>

                <div className="rounded-xl border border-border bg-background p-4">

                  <p className="text-muted-foreground">
                    AI Insights Generated
                  </p>

                  <h3 className="text-4xl font-bold text-foreground">
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