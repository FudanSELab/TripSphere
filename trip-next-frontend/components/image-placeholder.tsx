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
        "flex items-center justify-center bg-gray-100 from-slate-100 to-slate-200 text-slate-400",
        className,
      )}
    >
      <ImageIcon className={cn("size-12", iconClassName)} strokeWidth={1} />
    </div>
  );
}
