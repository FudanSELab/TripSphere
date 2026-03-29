import Image from "next/image";

export function HomeAtmosphereStrip() {
  return (
    <div
      aria-hidden
      className="border-border/40 pointer-events-none relative h-45 w-full overflow-hidden rounded-xl border sm:h-28 md:h-45"
    >
      <Image
        src="/images/john-rodenn-castillo-rQqWOHZ96OM-unsplash.jpg"
        alt=""
        fill
        className="object-cover object-[30%_20%]"
        sizes="(max-width: 768px) 100vw, min(1200px, 100vw)"
      />
      <div
        className="from-background/45 to-background/10 pointer-events-none absolute inset-0 bg-gradient-to-t via-transparent"
        aria-hidden
      />
    </div>
  );
}
