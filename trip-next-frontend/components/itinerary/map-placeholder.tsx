import { MapPin } from "lucide-react";

export function MapPlaceholder() {
  return (
    <div className="from-primary/5 via-primary/10 to-primary/15 relative flex h-full items-center justify-center overflow-hidden bg-gradient-to-br">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(var(--color-border) 1px, transparent 1px), linear-gradient(to right, var(--color-border) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />
      <div
        aria-hidden
        className="bg-primary/10 absolute -top-20 -left-20 size-72 rounded-full blur-3xl"
      />
      <div
        aria-hidden
        className="bg-primary/10 absolute -right-16 -bottom-16 size-64 rounded-full blur-3xl"
      />
      <div className="relative z-10 flex flex-col items-center gap-3 text-center">
        <div className="bg-background/70 rounded-2xl p-5 shadow-sm backdrop-blur-sm">
          <MapPin
            className="text-primary/60 mx-auto size-10"
            strokeWidth={1.5}
          />
        </div>
        <p className="text-foreground text-sm font-semibold">地图视图</p>
        <p className="text-muted-foreground max-w-[180px] text-xs leading-relaxed">
          高德地图 SDK 接入后将在此展示行程路线与景点
        </p>
      </div>
    </div>
  );
}
