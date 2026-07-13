interface Props {
  children: React.ReactNode;
}

export default function Container({ children }: Props) {
  return (
    <div className="mx-auto max-w-content px-6 lg:px-8">
      {children}
    </div>
  );
}