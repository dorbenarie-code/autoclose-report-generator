import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import clsx from "clsx";

export type KpiCardProps = {
  /** Card title (e.g. "Total Reports") */
  title: string;
  /** Numeric or textual KPI value */
  value: number | string;
  /** Controls text color: primary (blue), critical (red), success (green) */
  color?: "primary" | "critical" | "success";
  /** Number of grid columns to span (1–12) */
  span?: number;
};

const COLOR_CLASSES: Record<NonNullable<KpiCardProps["color"]>, string> = {
  primary: "text-blue-600",
  critical: "text-red-600",
  success: "text-green-600",
};

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  color = "primary",
  span = 3,
}) => {
  const spanClass = `col-span-${span}`;

  return (
    <div className={clsx(spanClass)}>
      <Card className="h-full shadow-sm border border-gray-200">
        <CardContent className="p-4 flex flex-col justify-between h-full">
          <div className="text-sm text-gray-500">{title}</div>
          <div
            className={clsx(
              "text-2xl font-semibold mt-2",
              COLOR_CLASSES[color]
            )}
          >
            {value}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
