"use client";

import { Avatar } from "@/components/ui/avatar";
import { useAuth } from "@/lib/hooks/use-auth";
import { useChatSidebar } from "@/lib/hooks/use-chat-sidebar";
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
    <header className="sticky top-0 right-0 left-0 z-40 w-full bg-white shadow-sm">
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="group flex items-center gap-2">
            <div className="from-primary-500 to-secondary-500 flex h-10 w-10 items-center justify-center rounded-xl bg-linear-to-br text-xl font-bold text-white shadow-lg transition-transform group-hover:scale-105">
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
                      ? "bg-primary-100 text-primary-700"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
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
                className="from-primary-500 to-secondary-500 flex items-center gap-2 rounded-lg bg-linear-to-r px-4 py-2 text-sm font-medium text-white transition-all duration-200 hover:scale-105 hover:shadow-lg"
                onClick={openAiAssistant}
              >
                <MessageSquare className="h-4 w-4" />
                AI Assistant
              </button>
            )}

            {/* User menu */}
            {auth.isAuthenticated ? (
              <div className="group relative">
                <button className="flex items-center gap-2 rounded-lg p-1.5 transition-colors hover:bg-gray-100">
                  <Avatar name={auth.user?.username} size="sm" />
                  <span className="text-sm font-medium text-gray-700">
                    {auth.user?.username}
                  </span>
                </button>

                {/* Dropdown */}
                <div className="invisible absolute top-full right-0 mt-2 w-48 rounded-xl border border-gray-100 bg-white opacity-0 shadow-lg transition-all duration-200 group-hover:visible group-hover:opacity-100">
                  <div className="p-2">
                    <Link
                      href="/profile"
                      className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-100"
                    >
                      <User className="h-4 w-4" />
                      Profile
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-red-600 transition-colors hover:bg-red-50"
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
                  className="px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:text-gray-900"
                >
                  Login
                </Link>
                <Link
                  href="/register"
                  className="bg-primary-600 hover:bg-primary-700 rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors"
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
