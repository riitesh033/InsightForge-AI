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
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm transition-all duration-300 hover:-translate-y-2 hover:shadow-xl">

      <div className="mb-6 text-5xl text-indigo-600">
        "
      </div>

      <p className="leading-7 text-slate-600">
        {message}
      </p>

      <div className="mt-8 border-t border-slate-200 pt-6">
        <h3 className="font-bold">
          {name}
        </h3>

        <p className="text-sm text-slate-500">
          {role}
        </p>
      </div>

    </div>
  );
}