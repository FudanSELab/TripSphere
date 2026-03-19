import {
  Wifi,
  Car,
  Utensils,
  Dumbbell,
  Waves,
  CheckCircle,
} from "lucide-react";

const AMENITY_PATTERNS: [string[], React.ElementType][] = [
  [["wifi", "网络", "宽带"], Wifi],
  [["停车", "车"], Car],
  [["餐", "厨", "早"], Utensils],
  [["健身", "运动"], Dumbbell],
  [["泳", "池"], Waves],
];

export function AmenityIcon({
  name,
  className,
}: {
  name: string;
  className?: string;
}) {
  const key = name.toLowerCase();
  for (const [patterns, Icon] of AMENITY_PATTERNS) {
    if (patterns.some((p) => key.includes(p))) {
      return <Icon className={className} />;
    }
  }
  return <CheckCircle className={className} />;
}
