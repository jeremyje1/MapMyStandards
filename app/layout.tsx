import './globals.css';
import { ReactNode } from 'react';

export const metadata = {
  title: 'MapMyStandards',
  description: 'Accreditation alignment & AI evidence mapping',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <header className="border-b bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/70 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto flex items-center justify-between px-4 py-3">
            <a href="/" className="font-semibold text-lg tracking-tight">MapMyStandards</a>
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
              <a className="hover:text-indigo-600" href="/services/">Services</a>
              <a className="hover:text-indigo-600" href="/about/">About</a>
              <a className="hover:text-indigo-600" href="/user-guide/">User Guide</a>
              <a className="hover:text-indigo-600" href="/contact/">Contact</a>
              <a className="hover:text-indigo-600" href="/privacy-policy/">Privacy</a>
              <a className="rounded bg-emerald-600 text-white px-3 py-1.5 hover:bg-emerald-500 transition" href="/landing?tier=department">Start Trial</a>
            </nav>
          </div>
        </header>
        <main className="p-6 max-w-7xl mx-auto">{children}</main>
      </body>
    </html>
  );
}
