"use client";

import { useAgentContext } from "@copilotkit/react-core/v2";
import type { ReviewTargetType } from "@/lib/review/types";

interface ReviewTargetContextProps {
  targetId: string;
  targetType: ReviewTargetType;
  targetName: string;
}

export function ReviewTargetContext({
  targetId,
  targetType,
  targetName,
}: ReviewTargetContextProps) {
  useAgentContext({
    description: "review target context",
    value: { targetId, targetType, targetName },
  });

  return null;
}
