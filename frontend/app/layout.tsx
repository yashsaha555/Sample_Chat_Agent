import "./globals.css";
import { ReactNode } from "react";
import { Plus_Jakarta_Sans } from "next/font/google";

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-pjs",
  display: "swap"
});

export const metadata = {
  title: "Contextual Assistant",
  description: "RAG Based Assistant"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={plusJakarta.variable}>
      <body className="bg-bg text-text antialiased font-sans">{children}</body>
    </html>
  );
}
