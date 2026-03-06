import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import { CopilotProvider } from "@/components/copilot-provider";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider
      defaultOpen={true}
      style={
        {
          "--sidebar-width": "10rem",
          "--sidebar-width-mobile": "10rem",
        } as React.CSSProperties
      }
    >
      <AppSidebar />
      <SidebarInset>
        <SiteHeader />
        <main className="mx-auto w-full max-w-screen-2xl px-[10rem] py-6">
          <CopilotProvider>{children}</CopilotProvider>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
