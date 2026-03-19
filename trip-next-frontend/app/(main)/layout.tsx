import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import { CopilotSidebar } from "@copilotkit/react-core/v2";

const COPILOT_LABELS = {
  modalHeaderTitle: "AI旅行助手",
  chatInputPlaceholder: "询问我任何旅游相关的问题",
};

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
          {children}
          <CopilotSidebar
            agentId="default"
            defaultOpen={true}
            width="30rem"
            labels={COPILOT_LABELS}
            autoFocus={true}
          />
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
