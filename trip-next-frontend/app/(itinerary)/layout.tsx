import { SiteHeader } from "@/components/site-header";

export default function ItineraryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-screen-2xl px-[10rem] py-6">
        {children}
      </main>
    </>
  );
}
