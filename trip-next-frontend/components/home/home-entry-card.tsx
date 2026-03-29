import Link from "next/link";
import type { LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type HomeEntryCardProps = {
  title: string;
  description: string;
  href: string;
  ctaLabel: string;
  icon: LucideIcon;
};

export function HomeEntryCard({
  title,
  description,
  href,
  ctaLabel,
  icon: Icon,
}: HomeEntryCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-col gap-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-2">
            <Icon className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="text-lg">{title}</CardTitle>
          </div>
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardFooter>
        <Button asChild variant="outline" className="w-fit">
          <Link href={href}>{ctaLabel}</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
