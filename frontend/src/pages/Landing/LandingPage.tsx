import Navbar from "@/components/landing/Navbar";
import Hero from "@/components/landing/Hero";
import Features from "@/components/landing/Features";
import HowItWorks from "@/components/landing/HowItWorks";
import Statistics from "@/components/landing/Statistics";
import Testimonials from "@/components/landing/Testimonials";

export default function LandingPage() {
  return (
    <>
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <Statistics />
      <Testimonials />
    </>
  );
}