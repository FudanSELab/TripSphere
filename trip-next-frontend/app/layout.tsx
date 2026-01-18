import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { ConditionalFooter } from "@/components/layout/conditional-footer";
import { Header } from "@/components/layout/header";
import { AuthProvider } from "@/components/providers/auth-provider";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TripSphere - AI Travel Assistant",
  description:
    "TripSphere is an intelligent travel planning platform powered by AI. Discover attractions, plan itineraries, and create travel memories with our smart assistant.",
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
          <div className="flex min-h-screen flex-col">
            <Header />
            <main className="flex-1">{children}</main>
            <ConditionalFooter />
            <ChatSidebar />
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
