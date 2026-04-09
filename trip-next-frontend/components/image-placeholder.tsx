import { ImageIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface ImagePlaceholderProps {
  className?: string;
  iconClassName?: string;
}

export function ImagePlaceholder({
  className,
  iconClassName,
}: ImagePlaceholderProps) {
  return (
    <div
      className={cn(
        "bg-muted text-muted-foreground flex items-center justify-center",
        className,
      )}
    >
      <ImageIcon className={cn("size-12", iconClassName)} strokeWidth={1} />
    </div>
  );
}
