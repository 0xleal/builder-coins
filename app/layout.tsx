import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Providers from "@/lib/providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Builders Fund",
  description: "Permissionless Index Fund for Web3 Builders",
};

export default function RootLayout({
  children,
  navbar,
  footer,
}: Readonly<{
  children: React.ReactNode;
  navbar: React.ReactNode;
  footer: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Providers>
          <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            {navbar}
            {children}
            {footer}
          </main>
        </Providers>
      </body>
    </html>
  );
}
