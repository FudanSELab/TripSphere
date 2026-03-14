import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import { CopilotKit } from "@copilotkit/react-core";

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
          <CopilotKit runtimeUrl="/api/v1/copilotkit">
            {children}
          </CopilotKit>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
