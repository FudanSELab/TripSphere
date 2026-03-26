import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import { CopilotSidebar } from "@copilotkit/react-core/v2";

const COPILOT_LABELS = {
  modalHeaderTitle: "AI 旅行助手",
  chatInputPlaceholder: "输入你的旅行需求：目的地/时间/偏好，我来帮你规划",
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
        <main className="mx-auto w-full max-w-screen-2xl px-4 py-6 sm:px-8 lg:px-16">
          {children}
          <CopilotSidebar
            agentId="default"
            defaultOpen={true}
            width="30rem"
            labels={COPILOT_LABELS}
          />
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
