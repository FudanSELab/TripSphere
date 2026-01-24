import { ChatSidebar } from "@/components/chat-sidebar";
import { ConditionalFooter } from "@/components/layout/conditional-footer";
import { Header } from "@/components/layout/header";
import { AuthProvider } from "@/components/providers/auth-provider";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TripSphere - AI-Native Travel Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body className="antialiased">
        <AuthProvider>
          <div className="relative flex min-h-screen flex-col">
            <Header />
            <main className="flex flex-1 flex-col">{children}</main>
            <ConditionalFooter />
            <ChatSidebar />
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
