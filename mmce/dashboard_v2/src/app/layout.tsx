import type { Metadata } from "next";
import { Playfair_Display, Fira_Code } from "next/font/google";
import "./globals.css";

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
});

const firaCode = Fira_Code({
  variable: "--font-fira",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MMCE Thoroughness Dashboard",
  description: "Academic evaluation dashboard for Thoroughness Bench",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${playfair.variable} ${firaCode.variable} h-full antialiased`}
    >
      <body className="h-full bg-paper text-ink font-mono tracking-tight selection:bg-sage selection:text-paper">
        {children}
      </body>
    </html>
  );
}
