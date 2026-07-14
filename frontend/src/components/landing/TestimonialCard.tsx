type TestimonialCardProps = {
  name: string;
  role: string;
  message: string;
};

export default function TestimonialCard({
  name,
  role,
  message,
}: TestimonialCardProps) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm transition-all duration-300 hover:-translate-y-2 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900">

      {/* Quote */}

      <div className="mb-6 text-5xl font-bold text-indigo-600 dark:text-indigo-400">
        "
      </div>

      {/* Message */}

      <p className="leading-7 text-slate-600 dark:text-slate-300">
        {message}
      </p>

      {/* Author */}

      <div className="mt-8 border-t border-slate-200 pt-6 dark:border-slate-700">

        <h3 className="font-bold text-slate-900 dark:text-white">
          {name}
        </h3>

        <p className="text-sm text-slate-500 dark:text-slate-400">
          {role}
        </p>

      </div>

    </div>
  );
}