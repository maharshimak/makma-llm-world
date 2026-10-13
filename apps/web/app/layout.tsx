import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: "Mak'ma · Research civilization", description: 'Local research agents, reproducible experiments, and human control.' };
export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en" className="dark"><body>{children}</body></html>;
}
