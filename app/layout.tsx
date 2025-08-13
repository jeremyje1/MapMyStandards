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
        <header className="p-4 border-b bg-white"><h1 className="font-semibold">MapMyStandards</h1></header>
        <main className="p-6">{children}</main>
      </body>
    </html>
  );
}
