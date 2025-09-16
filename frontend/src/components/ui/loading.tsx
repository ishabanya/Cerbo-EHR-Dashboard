import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

// Loading Spinner Component
const spinnerVariants = cva(
  "animate-spin rounded-full border-2 border-current border-t-transparent",
  {
    variants: {
      size: {
        sm: "h-4 w-4",
        default: "h-6 w-6",
        lg: "h-8 w-8",
        xl: "h-12 w-12",
      },
      variant: {
        default: "text-primary",
        secondary: "text-secondary",
        medical: "text-medical-blue",
      },
    },
    defaultVariants: {
      size: "default",
      variant: "default",
    },
  }
)

export interface LoadingSpinnerProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof spinnerVariants> {
  text?: string
}

const LoadingSpinner = React.forwardRef<HTMLDivElement, LoadingSpinnerProps>(
  ({ className, size, variant, text, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex items-center justify-center", className)}
      role="status"
      aria-label={text || "Loading"}
      {...props}
    >
      <div className={cn(spinnerVariants({ size, variant }))} />
      {text && <span className="ml-2 text-sm text-muted-foreground">{text}</span>}
      <span className="sr-only">{text || "Loading..."}</span>
    </div>
  )
)
LoadingSpinner.displayName = "LoadingSpinner"

// Loading Dots Component
const LoadingDots: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("flex space-x-1", className)}>
    {[0, 1, 2].map((i) => (
      <div
        key={i}
        className="h-2 w-2 bg-current rounded-full animate-pulse"
        style={{
          animationDelay: `${i * 0.1}s`,
          animationDuration: "0.6s",
        }}
      />
    ))}
  </div>
)

// Skeleton Components
const skeletonVariants = cva(
  "animate-pulse bg-muted rounded",
  {
    variants: {
      variant: {
        default: "bg-muted",
        card: "bg-muted/50",
        text: "bg-muted/80",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface SkeletonProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof skeletonVariants> {}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, variant, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(skeletonVariants({ variant, className }))}
      {...props}
    />
  )
)
Skeleton.displayName = "Skeleton"

// Skeleton variants for common UI elements
const SkeletonText: React.FC<{ lines?: number; className?: string }> = ({ 
  lines = 3, 
  className 
}) => (
  <div className={cn("space-y-2", className)}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        variant="text"
        className={cn(
          "h-4",
          i === lines - 1 ? "w-3/4" : "w-full"
        )}
      />
    ))}
  </div>
)

const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("space-y-4 p-6 border rounded-lg", className)}>
    <div className="flex items-center space-x-4">
      <Skeleton className="h-12 w-12 rounded-full" />
      <div className="space-y-2 flex-1">
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-3 w-1/3" />
      </div>
    </div>
    <SkeletonText lines={3} />
  </div>
)

const SkeletonTable: React.FC<{ 
  rows?: number
  columns?: number
  className?: string 
}> = ({ 
  rows = 5, 
  columns = 4, 
  className 
}) => (
  <div className={cn("space-y-3", className)}>
    {/* Header */}
    <div className="flex space-x-4">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} className="h-4 flex-1" />
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div key={rowIndex} className="flex space-x-4">
        {Array.from({ length: columns }).map((_, colIndex) => (
          <Skeleton key={colIndex} className="h-6 flex-1" />
        ))}
      </div>
    ))}
  </div>
)

// Medical-specific loading components
const PatientCardSkeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("medical-card space-y-4", className)}>
    <div className="flex items-center space-x-4">
      <Skeleton className="h-16 w-16 rounded-full" />
      <div className="space-y-2 flex-1">
        <Skeleton className="h-5 w-1/2" />
        <Skeleton className="h-3 w-1/3" />
        <Skeleton className="h-3 w-1/4" />
      </div>
    </div>
    <div className="grid grid-cols-2 gap-4">
      <div className="space-y-2">
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-4 w-3/4" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    </div>
  </div>
)

const AppointmentCardSkeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("medical-card space-y-3", className)}>
    <div className="flex justify-between items-start">
      <div className="space-y-2 flex-1">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
      <Skeleton className="h-6 w-20 rounded-full" />
    </div>
    <div className="flex space-x-4">
      <Skeleton className="h-3 w-1/4" />
      <Skeleton className="h-3 w-1/4" />
    </div>
  </div>
)

const VitalsGridSkeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("vitals-grid", className)}>
    {Array.from({ length: 4 }).map((_, i) => (
      <div key={i} className="vitals-card space-y-2">
        <Skeleton className="h-8 w-16 mx-auto" />
        <Skeleton className="h-3 w-20 mx-auto" />
      </div>
    ))}
  </div>
)

// Loading screen component
const LoadingScreen: React.FC<{
  text?: string
  className?: string
}> = ({ text = "Loading...", className }) => (
  <div className={cn(
    "flex flex-col items-center justify-center min-h-screen bg-background",
    className
  )}>
    <LoadingSpinner size="xl" text={text} />
  </div>
)

export {
  LoadingSpinner,
  LoadingDots,
  Skeleton,
  SkeletonText,
  SkeletonCard,
  SkeletonTable,
  PatientCardSkeleton,
  AppointmentCardSkeleton,
  VitalsGridSkeleton,
  LoadingScreen,
  spinnerVariants,
  skeletonVariants,
}