import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-svh">
      <Button
        variant="ghost"
        size="sm"
        className="absolute top-4 left-4"
        asChild
      >
        <Link href="/">
          <ArrowLeft className="size-4" />
          返回首页
        </Link>
      </Button>
      {children}
    </div>
  );
}
