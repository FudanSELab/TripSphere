"use client";

import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { useAuth } from "@/hooks/use-auth";
import { useChatSidebar } from "@/hooks/use-chat-sidebar";
import {
  Bot,
  Calendar,
  FileText,
  Hotel,
  LogOut,
  MapPin,
  MessageSquare,
  User,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const navLinks = [
  { name: "Chat", path: "/chat", icon: Bot },
  { name: "Attractions", path: "/attractions", icon: MapPin },
  { name: "Hotels", path: "/hotels", icon: Hotel },
  { name: "Itinerary", path: "/itinerary", icon: Calendar },
  { name: "Notes", path: "/notes", icon: FileText },
];

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const auth = useAuth();
  const chatSidebar = useChatSidebar();

  const isActive = (path: string) => {
    return pathname === path || pathname.startsWith(path + "/");
  };

  const handleLogout = async () => {
    await auth.logout();
    router.push("/login");
  };

  const openAiAssistant = () => {
    chatSidebar.open();
  };

  return (
    <header className="bg-background sticky top-0 right-0 left-0 z-50 w-full shadow-sm">
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="group flex items-center gap-2">
            <div className="bg-primary text-primary-foreground flex h-10 w-10 items-center justify-center rounded-xl text-xl font-bold shadow-lg transition-transform group-hover:scale-105">
              T
            </div>
            <span className="gradient-text text-xl font-bold">TripSphere</span>
          </Link>

          {/* Navigation */}
          <div className="flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              return (
                <Link
                  key={link.path}
                  href={link.path}
                  className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
                    isActive(link.path)
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {link.name}
                </Link>
              );
            })}
          </div>

          {/* Right side actions */}
          <div className="flex items-center gap-3">
            {/* Chat button - hidden on /chat page */}
            {pathname !== "/chat" && (
              <button
                className="bg-primary text-primary-foreground flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 hover:scale-105 hover:shadow-lg"
                onClick={openAiAssistant}
              >
                <MessageSquare className="h-4 w-4" />
                AI Assistant
              </button>
            )}

            {/* User menu */}
            {auth.isAuthenticated ? (
              <div className="group relative">
                <button className="hover:bg-muted flex items-center gap-2 rounded-lg p-1.5 transition-colors">
                  <Avatar>
                    <AvatarImage src="https://i.pravatar.cc/300" />
                  </Avatar>
                  <span className="text-foreground text-sm font-medium">
                    {auth.user?.username}
                  </span>
                </button>

                {/* Dropdown */}
                <div className="border-border bg-background invisible absolute top-full right-0 mt-2 w-48 rounded-xl border opacity-0 shadow-lg transition-all duration-200 group-hover:visible group-hover:opacity-100">
                  <div className="p-2">
                    <Link
                      href="/profile"
                      className="text-foreground hover:bg-muted flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors"
                    >
                      <User className="h-4 w-4" />
                      Profile
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="text-destructive hover:bg-destructive/10 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors"
                    >
                      <LogOut className="h-4 w-4" />
                      Logout
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="text-foreground hover:text-foreground/80 px-4 py-2 text-sm font-medium transition-colors"
                >
                  Login
                </Link>
                <Link
                  href="/signup"
                  className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </nav>
    </header>
  );
}
