import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Story Analyzer",
  description: "Validate user stories for delivery readiness.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
