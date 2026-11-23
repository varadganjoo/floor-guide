import type { Metadata } from "next";
import "@astryxdesign/core/reset.css";
import "@astryxdesign/core/astryx.css";
import "@astryxdesign/theme-neutral/theme.css";
import "@astryxdesign/theme-neutral/fonts.css";
import { Providers } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Floor Guide · Document assistant",
  description: "A document assistant for floor supervisors, with source evidence and run inspection.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="light" suppressHydrationWarning>
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
