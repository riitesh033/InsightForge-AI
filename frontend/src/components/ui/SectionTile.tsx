interface Props {
  title: string;
  subtitle?: string;
}

export default function SectionTitle({
  title,
  subtitle,
}: Props) {
  return (
    <div className="mx-auto mb-14 max-w-2xl text-center">
      <h2 className="text-4xl font-bold">
        {title}
      </h2>

      {subtitle && (
        <p className="mt-4 text-slate-600">
          {subtitle}
        </p>
      )}
    </div>
  );
}