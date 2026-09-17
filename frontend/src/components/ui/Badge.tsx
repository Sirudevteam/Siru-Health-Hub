import { clsx } from 'clsx';

type Variant = 'green' | 'red' | 'blue' | 'gray' | 'yellow';

const variants: Record<Variant, string> = {
  green:  'bg-green-100 text-green-800',
  red:    'bg-red-100 text-red-800',
  blue:   'bg-blue-100 text-blue-800',
  gray:   'bg-gray-100 text-gray-800',
  yellow: 'bg-yellow-100 text-yellow-800',
};

export function Badge({
  children,
  variant = 'gray',
}: {
  children: React.ReactNode;
  variant?: Variant;
}) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        variants[variant]
      )}
    >
      {children}
    </span>
  );
}
