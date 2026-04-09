import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { CopilotProvider } from "@/components/copilot-provider";
import "@copilotkit/react-core/v2/styles.css";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "TripSphere",
    template: "%s - TripSphere",
  },
  description: "AI-Native Travel Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" data-scroll-behavior="smooth">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <CopilotProvider>{children}</CopilotProvider>
      </body>
    </html>
  );
}
