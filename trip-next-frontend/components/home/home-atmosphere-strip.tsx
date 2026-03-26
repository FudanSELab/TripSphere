import Image from "next/image";

/**
 * Decorative panorama strip — no copy on the image; bridges hero and content rhythm.
 */
export function HomeAtmosphereStrip() {
  return (
    <div
      aria-hidden
      className="pointer-events-none relative h-24 w-full overflow-hidden rounded-xl border border-border/40 sm:h-28 md:h-70"
    >
      <Image
        src="/images/scene2.png"
        alt=""
        fill
        className="object-cover object-[100%_50%]"
        sizes="(max-width: 768px) 100vw, min(1200px, 100vw)"
      />
      <div
        className="pointer-events-none absolute inset-0 bg-gradient-to-t from-background/45 via-transparent to-background/10"
        aria-hidden
      />
    </div>
  );
}
