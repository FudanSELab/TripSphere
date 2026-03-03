import { CopilotKit } from "@copilotkit/react-core";
import { SiteHeader } from "@/components/site-header";

export default function ItineraryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <SiteHeader />
      <CopilotKit runtimeUrl="/api/v1/copilotkit">{children}</CopilotKit>
    </>
  );
}
