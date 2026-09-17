import type { Metadata } from 'next';
import './globals.css';
import { Navbar } from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'Siru HealthHub',
  description: 'FHIR Healthcare Platform — FHIR R4 Compliant Patient Portal',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-gray-50">
        <Navbar />

        <main className="flex-1">
          {children}
        </main>

        <footer className="bg-emerald-800 text-emerald-100 py-4 mt-auto">
          <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-sm">
            <span>© 2026 Siru HealthHub — FHIR R4 Compliant Platform</span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-400" />
              HL7 FHIR R4 (4.0.1)
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
