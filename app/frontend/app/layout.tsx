import type { Metadata } from "next";
import { Public_Sans, Space_Grotesk } from "next/font/google";

import "./globals.css";

const publicSans = Public_Sans({
  variable: "--font-public-sans",
  subsets: ["latin"],
});
const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CloudAITrader",
  description: "Prop-firm-aware crypto backtesting",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${publicSans.variable} ${spaceGrotesk.variable}`}>
        {children}
      </body>
    </html>
  );
}
