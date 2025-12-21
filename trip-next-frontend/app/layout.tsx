import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { Footer } from "@/components/layout/footer";
import { Header } from "@/components/layout/header";
import LoadingBar from "@/components/layout/loading-bar";
import type { Metadata } from "next";
import { Suspense } from "react";
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
        <Suspense fallback={null}>
          <LoadingBar />
        </Suspense>
        <div className="flex min-h-screen flex-col">
          <Header />
          <main className="flex-1 pt-16">{children}</main>
          <Footer />
          <ChatSidebar />
        </div>
      </body>
    </html>
  );
}
