import { Search } from "lucide-react";

interface Props {
  value: string;
  onChange: (value: string) => void;
}

export default function DatasetSearch({
  value,
  onChange,
}: Props) {
  return (
    <div className="relative max-w-md">
      <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />

      <input
        value={value}
        onChange={(e) =>
          onChange(e.target.value)
        }
        placeholder="Search datasets..."
        className="w-full rounded-xl border bg-background py-2 pl-10 pr-4 outline-none transition focus:border-primary"
      />
    </div>
  );
}