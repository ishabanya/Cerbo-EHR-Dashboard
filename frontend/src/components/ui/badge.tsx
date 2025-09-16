import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        // Medical/Healthcare specific variants
        active: "border-transparent bg-green-100 text-green-800",
        inactive: "border-transparent bg-gray-100 text-gray-800",
        scheduled: "border-transparent bg-blue-100 text-blue-800",
        confirmed: "border-transparent bg-green-100 text-green-800",
        cancelled: "border-transparent bg-red-100 text-red-800",
        completed: "border-transparent bg-gray-100 text-gray-800",
        "in-progress": "border-transparent bg-yellow-100 text-yellow-800",
        urgent: "border-transparent bg-red-100 text-red-800",
        high: "border-transparent bg-red-100 text-red-800",
        medium: "border-transparent bg-yellow-100 text-yellow-800",
        low: "border-transparent bg-green-100 text-green-800",
        success: "border-transparent bg-status-success text-white",
        warning: "border-transparent bg-status-warning text-white",
        error: "border-transparent bg-status-error text-white",
        info: "border-transparent bg-status-info text-white",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }