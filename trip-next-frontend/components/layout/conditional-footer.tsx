"use client";

import { Footer } from "@/components/layout/footer";
import { usePathname } from "next/navigation";

export function ConditionalFooter() {
  const pathname = usePathname();

  // These pages do not display Footer
  const hiddenFooterPaths = ["/chat", "/login", "/signup"];

  // Check if pathname is a subpath of hiddenFooterPaths
  const shouldHideFooter = hiddenFooterPaths.includes(pathname);

  if (shouldHideFooter) {
    return null;
  }

  return <Footer />;
}
