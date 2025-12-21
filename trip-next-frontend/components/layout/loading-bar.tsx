"use client";

import { AnimatePresence, motion } from "framer-motion";
import { usePathname, useSearchParams } from "next/navigation";
import { startTransition, useEffect, useState } from "react";

export default function LoadingBar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    startTransition(() => {
      setIsLoading(true);
    });
    const timer = setTimeout(() => {
      startTransition(() => {
        setIsLoading(false);
      });
    }, 400);
    return () => clearTimeout(timer);
  }, [pathname, searchParams]);

  return (
    <AnimatePresence>
      {isLoading && (
        <motion.div
          initial={{ scaleX: 0, opacity: 0.5 }}
          animate={{ scaleX: 1, opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4, ease: "easeInOut" }}
          className="from-primary-500 via-secondary-500 to-accent-500 fixed top-0 right-0 left-0 z-50 h-1 origin-left bg-gradient-to-r"
        />
      )}
    </AnimatePresence>
  );
}
