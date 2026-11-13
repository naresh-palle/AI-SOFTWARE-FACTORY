import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/lib/providers";

export const metadata: Metadata = {
  title: "AI Software Factory - Enterprise Management Dashboard",
  description: "Autonomous Multi-Agent AI Software Engineering Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased font-sans min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
