'use client'

import { motion } from 'framer-motion'
import { useEffect } from 'react'

const pageVariants = {
  initial: {
    opacity: 0,
    y: 0,
    filter: 'blur(4px)',
  },
  animate: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: {
      duration: 0.5,
      ease: [0.22, 1, 0.36, 1] as const,
      filter: {
        duration: 0.3,
      },
    },
  },
}

export default function Template({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Scroll to top on route change
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [])

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      style={{ width: '100%', willChange: 'transform, opacity' }}
    >
      {children}
    </motion.div>
  )
}
