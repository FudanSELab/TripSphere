import { SiteHeader } from "@/components/site-header";
import { CopilotProvider } from "@/components/copilot-provider";

export default function ItineraryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <SiteHeader />
      <CopilotProvider>
        <main className="mx-auto w-full max-w-screen-2xl px-[10rem] py-6">
          {children}
        </main>
      </CopilotProvider>
    </>
  );
}
