"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";
import type { SessionPayload } from "@/lib/definitions";

// Hydration fix: NavigationMenu internally generates unique IDs that differ
// between server and client, so we skip SSR entirely and render a skeleton placeholder.
const UserNavigationMenu = dynamic(
  () =>
    import("@/components/user-navigation-menu").then(
      (mod) => mod.UserNavigationMenu,
    ),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center gap-2 px-2">
        <Skeleton className="size-8 rounded-full" />
        <Skeleton className="hidden h-4 w-16 md:block" />
      </div>
    ),
  },
);

interface UserNavigationProps {
  user: SessionPayload;
}

export function UserNavigation({ user }: UserNavigationProps) {
  return <UserNavigationMenu user={user} />;
}
