export function Card({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-white rounded-lg shadow border border-gray-200 p-6 ${className}`}>
      {children}
    </div>
  );
}
