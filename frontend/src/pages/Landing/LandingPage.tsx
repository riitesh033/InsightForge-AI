import Navbar from "@/components/landing/Navbar";
import Hero from "@/components/landing/Hero";
import Features from "@/components/landing/Features";
import HowItWorks from "@/components/landing/HowItWorks";
import Statistics from "@/components/landing/Statistics";
import Testimonials from "@/components/landing/Testimonials";
import Pricing from "@/components/landing/Pricing";
import FAQ from "@/components/landing/FAQ";
import CTA from "@/components/landing/CTA";
import Footer from "@/components/landing/Footer";
import BackToTop from "@/components/common/BackToTop";

export default function LandingPage() {
  return (
    <main className="relative overflow-hidden bg-background">

      {/* Background Glow */}
      <div className="absolute inset-0 -z-10 overflow-hidden">

        <div
          className="
            absolute
            top-[-250px]
            left-1/2
            h-[900px]
            w-[900px]
            -translate-x-1/2
            rounded-full
            bg-cyan-500/10
            blur-[180px]
          "
        />

        <div
          className="
            absolute
            bottom-[-300px]
            right-[-150px]
            h-[700px]
            w-[700px]
            rounded-full
            bg-indigo-500/10
            blur-[180px]
          "
        />

      </div>

      <Navbar />

      <Hero />

      <Features />

      <HowItWorks />

      <Statistics />

      <Testimonials />

      <Pricing />

      <FAQ />

      <CTA />

      <Footer />

      <BackToTop />

    </main>
  );
}