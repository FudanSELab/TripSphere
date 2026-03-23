import { SiteHeader } from "@/components/site-header";

export default function ItineraryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <SiteHeader />
      <main className="w-full">{children}</main>
    </>
  );
}
