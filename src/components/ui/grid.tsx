import React from "react";

export type GridProps = {
  /** Number of columns (default: 12) */
  cols?: number;
  /** Gap between items in rem units (default: 1rem) */
  gap?: number;
  children: React.ReactNode;
  className?: string;
};

/**
 * Simple CSS Grid wrapper.
 * Uses inline styles for dynamic columns/gap without forcing Tailwind rebuild.
 */
export const Grid: React.FC<GridProps> = ({
  cols = 12,
  gap = 1,
  children,
  className = '',
}) => {
  const style: React.CSSProperties = {
    display: "grid",
    gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
    gap: `${gap}rem`,
  };

  return <div style={style} className={className}>{children}</div>;
}; 