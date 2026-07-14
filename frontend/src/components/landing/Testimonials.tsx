import TestimonialCard from "./TestimonialCard";

const testimonials = [
  {
    name: "Rahul Sharma",
    role: "Data Analyst",
    message:
      "InsightForge AI reduced my data cleaning time from hours to minutes.",
  },
  {
    name: "Priya Patel",
    role: "B.Sc Computer Science Student",
    message:
      "The AI insights helped me understand my datasets much faster.",
  },
  {
    name: "Arjun Mehta",
    role: "Research Scholar",
    message:
      "Interactive dashboards and PDF reports saved a lot of manual work.",
  },
];

export default function Testimonials() {
  return (
    <section id="testimonials" className="bg-white py-28 dark:bg-slate-950">
      <div className="mx-auto max-w-7xl px-6">

        {/* Section Heading */}
        <div className="mb-16 text-center">

          <span className="inline-block rounded-full bg-indigo-100 px-4 py-2 text-sm font-semibold text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
            Testimonials
          </span>

          <h2 className="mt-6 text-4xl font-bold text-slate-900 dark:text-white">
            What People Say
          </h2>

          <p className="mt-4 text-lg text-slate-600 dark:text-slate-400">
            Sample feedback showcasing the value of InsightForge AI.
          </p>

        </div>

        {/* Cards */}
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">

          {testimonials.map((testimonial) => (
            <TestimonialCard
              key={testimonial.name}
              {...testimonial}
            />
          ))}

        </div>

      </div>
    </section>
  );
}