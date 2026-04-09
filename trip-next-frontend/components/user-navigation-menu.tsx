"use client";

import * as React from "react";
import Link from "next/link";
import { Settings, LogOut, ChevronRight } from "lucide-react";
import { signOut } from "@/actions/auth";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from "@/components/ui/navigation-menu";
import type { SessionPayload } from "@/lib/definitions";

interface UserNavigationMenuProps {
  user: SessionPayload;
}

export function UserNavigationMenu({ user }: UserNavigationMenuProps) {
  // Get initials from name (first 2 characters)
  const initials = user.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <NavigationMenu viewport={false}>
      <NavigationMenuList>
        <NavigationMenuItem>
          <NavigationMenuTrigger className="hover:bg-accent data-[state=open]:bg-accent/50 gap-2 bg-transparent px-2">
            <Avatar size="sm">
              <AvatarImage
                src={`https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(user.name)}`}
                alt={user.name}
              />
              <AvatarFallback>{initials}</AvatarFallback>
            </Avatar>
            <span className="hidden max-w-24 truncate md:inline">
              {user.name}
            </span>
          </NavigationMenuTrigger>
          <NavigationMenuContent>
            <Link
              href="/profile"
              className="hover:bg-accent flex items-center gap-3 rounded-sm p-3 transition-colors"
            >
              <Avatar className="size-12">
                <AvatarImage
                  src={`https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(user.name)}`}
                  alt={user.name}
                />
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
              <div className="flex flex-1 flex-col gap-1">
                <p className="text-sm leading-none font-medium">{user.name}</p>
                <p className="text-muted-foreground text-xs leading-none">
                  {user.email}
                </p>
              </div>
              <ChevronRight className="text-muted-foreground size-4" />
            </Link>
            <Separator className="my-2" />
            <ul>
              <ListItem href="/account">
                <Settings className="size-4" />
                账户设置
              </ListItem>
              <li>
                <button
                  onClick={() => signOut()}
                  className="text-destructive hover:bg-destructive/10 flex w-full cursor-pointer items-center gap-2 rounded-sm p-2 text-sm"
                >
                  <LogOut className="size-4" />
                  退出登录
                </button>
              </li>
            </ul>
          </NavigationMenuContent>
        </NavigationMenuItem>
      </NavigationMenuList>
    </NavigationMenu>
  );
}

function ListItem({
  children,
  href,
  ...props
}: React.ComponentPropsWithoutRef<"li"> & {
  href: string;
}) {
  return (
    <li {...props}>
      <NavigationMenuLink asChild>
        <Link href={href}>
          <div className="flex items-center gap-2">{children}</div>
        </Link>
      </NavigationMenuLink>
    </li>
  );
}
