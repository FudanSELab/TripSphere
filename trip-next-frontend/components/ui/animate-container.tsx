"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface AnimateContainerProps {
  children: ReactNode;
  delay?: number;
  className?: string;
  stagger?: boolean;
}

// 单个元素的动画变体
export const fadeInUpVariants = {
  hidden: {
    opacity: 0,
    y: 20,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: [0.22, 1, 0.36, 1] as const,
    },
  },
};

// 交错动画容器的变体
export const staggerContainerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0,
    },
  },
};

// 单个动画元素
export function AnimateInView({
  children,
  delay = 0,
  className = "",
}: AnimateContainerProps) {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-100px" }}
      variants={fadeInUpVariants}
      transition={{ delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// 交错动画容器
export function StaggerContainer({
  children,
  className = "",
}: AnimateContainerProps) {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-100px" }}
      variants={staggerContainerVariants}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// 交错动画子元素
export function StaggerItem({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <motion.div variants={fadeInUpVariants} className={className}>
      {children}
    </motion.div>
  );
}
