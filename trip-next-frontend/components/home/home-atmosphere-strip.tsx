"use client";

import Image from "next/image";
import * as React from "react";
import Autoplay from "embla-carousel-autoplay";

import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
  type CarouselApi,
} from "@/components/ui/carousel";
import { cn } from "@/lib/utils";

type AtmosphereSlide = {
  src: string;
  alt: string;
  title: string;
  description: string;
  objectPosition: string;
};

const SLIDES: readonly AtmosphereSlide[] = [
  {
    src: "/images/CoNCb2nCdudZoD4gACOFhV80m_g.webp",
    alt: "埃及探秘",
    title: "埃及探秘",
    description: "追踪孕育古埃及文明的北纬30度",
    objectPosition: "50% 25%",
  },
  {
    src: "/images/CoNCb2nE-pMgT9SOAH4WxjYJxFM.webp",
    alt: "土库曼斯坦",
    title: "土库曼斯坦",
    description: "持续燃烧了50年的“地狱之门”",
    objectPosition: "50% 85%",
  },
  {
    src: "/images/CoNCXGm7siE_okMVABr400Q9yS4.webp",
    alt: "漫游杨苏沪",
    title: "漫游杨苏沪",
    description: "在江南的春风里书写温情时光",
    objectPosition: "50% 85%",
  },
];

export function HomeAtmosphereStrip() {
  const [api, setApi] = React.useState<CarouselApi>();
  const [current, setCurrent] = React.useState(0);

  const autoplay = React.useRef(
    Autoplay({ delay: 6500, stopOnInteraction: true, stopOnMouseEnter: true }),
  );

  React.useEffect(() => {
    if (!api) {
      return;
    }

    setCurrent(api.selectedScrollSnap());
    const onSelect = () => setCurrent(api.selectedScrollSnap());
    api.on("select", onSelect);

    return () => {
      api.off("select", onSelect);
    };
  }, [api]);

  return (
    <div className="flex w-full flex-col gap-2">
      <Carousel
        setApi={setApi}
        opts={{ loop: true, align: "start" }}
        plugins={[autoplay.current]}
        className="w-full"
        aria-label="氛围精选轮播"
      >
        <CarouselContent className="-ml-0">
          {SLIDES.map((slide, index) => (
            <CarouselItem key={slide.src} className="pl-0">
              <div
                className={cn(
                  "border-border/40 relative h-45 w-full overflow-hidden rounded-xl border",
                  "sm:h-28 md:h-45",
                )}
              >
                <Image
                  src={slide.src}
                  alt={slide.alt}
                  fill
                  className="object-cover"
                  style={{ objectPosition: slide.objectPosition }}
                  sizes="(max-width: 768px) 100vw, min(1200px, 100vw)"
                  priority={index === 0}
                />
                <div
                  className="from-background/10 via-background/5 pointer-events-none absolute inset-0 bg-gradient-to-r to-transparent"
                  aria-hidden
                />
                <div className="pointer-events-none absolute inset-0 flex items-center">
                  <div className="max-w-md pr-8 pl-[12%] md:pr-16 md:pl-[18%]">
                    <p className="text-xl font-semibold tracking-tight text-balance text-white drop-shadow-md md:text-3xl">
                      {slide.title}
                    </p>
                    <p className="mt-1.5 text-sm text-white/90 drop-shadow md:text-base">
                      {slide.description}
                    </p>
                  </div>
                </div>
              </div>
            </CarouselItem>
          ))}
        </CarouselContent>

        <CarouselPrevious
          type="button"
          variant="outline"
          className="top-1/2 left-3 z-10 -translate-y-1/2 border-white/35 bg-black/20 text-white shadow-sm hover:bg-black/35 hover:text-white dark:border-white/25"
        />
        <CarouselNext
          type="button"
          variant="outline"
          className="top-1/2 right-3 z-10 -translate-y-1/2 border-white/35 bg-black/20 text-white shadow-sm hover:bg-black/35 hover:text-white dark:border-white/25"
        />

        <div className="pointer-events-none absolute right-0 bottom-3 left-0 z-10 flex justify-center gap-1.5">
          {SLIDES.map((slide, index) => (
            <button
              key={slide.src}
              type="button"
              aria-label={`第 ${index + 1} 张，共 ${SLIDES.length} 张`}
              aria-current={index === current ? "true" : undefined}
              className={cn(
                "pointer-events-auto size-2 rounded-full transition-colors",
                index === current
                  ? "bg-white"
                  : "bg-white/45 hover:bg-white/70",
              )}
              onClick={() => api?.scrollTo(index)}
            />
          ))}
        </div>
      </Carousel>
      <p className="text-muted-foreground text-right text-xs">
        注：图片来自马蜂窝“历历在目”
      </p>
    </div>
  );
}
