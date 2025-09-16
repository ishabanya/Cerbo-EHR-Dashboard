import * as React from "react"
import * as TabsPrimitive from "@radix-ui/react-tabs"

import { cn } from "@/lib/utils"

const Tabs = TabsPrimitive.Root

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List> & {
    variant?: "default" | "pills" | "underline"
  }
>(({ className, variant = "default", ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center",
      {
        "rounded-md bg-muted p-1 text-muted-foreground": variant === "default",
        "space-x-2": variant === "pills",
        "border-b border-border": variant === "underline",
      },
      className
    )}
    {...props}
  />
))
TabsList.displayName = TabsPrimitive.List.displayName

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger> & {
    variant?: "default" | "pills" | "underline"
    icon?: React.ReactNode
  }
>(({ className, variant = "default", icon, children, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
      {
        // Default variant
        "rounded-sm px-3 py-1.5 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm": 
          variant === "default",
        // Pills variant
        "rounded-full px-4 py-2 bg-transparent hover:bg-accent hover:text-accent-foreground data-[state=active]:bg-primary data-[state=active]:text-primary-foreground": 
          variant === "pills",
        // Underline variant
        "px-4 py-2 border-b-2 border-transparent hover:text-foreground data-[state=active]:border-primary data-[state=active]:text-foreground": 
          variant === "underline",
      },
      className
    )}
    {...props}
  >
    {icon && <span className="mr-2">{icon}</span>}
    {children}
  </TabsPrimitive.Trigger>
))
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      className
    )}
    {...props}
  />
))
TabsContent.displayName = TabsPrimitive.Content.displayName

// Medical tabs with predefined structure
interface MedicalTabsProps {
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
  tabs: Array<{
    value: string
    label: string
    icon?: React.ReactNode
    content: React.ReactNode
    disabled?: boolean
  }>
  variant?: "default" | "pills" | "underline"
  className?: string
}

const MedicalTabs = React.forwardRef<
  React.ElementRef<typeof Tabs>,
  MedicalTabsProps
>(({ tabs, variant = "default", className, ...props }, ref) => (
  <Tabs ref={ref} className={cn("w-full", className)} {...props}>
    <TabsList variant={variant}>
      {tabs.map((tab) => (
        <TabsTrigger
          key={tab.value}
          value={tab.value}
          variant={variant}
          icon={tab.icon}
          disabled={tab.disabled}
        >
          {tab.label}
        </TabsTrigger>
      ))}
    </TabsList>
    {tabs.map((tab) => (
      <TabsContent key={tab.value} value={tab.value}>
        {tab.content}
      </TabsContent>
    ))}
  </Tabs>
))
MedicalTabs.displayName = "MedicalTabs"

// Patient record tabs component
interface PatientTabsProps {
  patientId: string
  defaultTab?: string
}

const PatientTabs: React.FC<PatientTabsProps> = ({ 
  patientId, 
  defaultTab = "overview" 
}) => {
  const patientTabs = [
    {
      value: "overview",
      label: "Overview",
      content: <div>Patient overview content for {patientId}</div>,
    },
    {
      value: "medical-history",
      label: "Medical History",
      content: <div>Medical history content for {patientId}</div>,
    },
    {
      value: "medications",
      label: "Medications",
      content: <div>Medications content for {patientId}</div>,
    },
    {
      value: "allergies",
      label: "Allergies",
      content: <div>Allergies content for {patientId}</div>,
    },
    {
      value: "vitals",
      label: "Vitals",
      content: <div>Vitals content for {patientId}</div>,
    },
    {
      value: "documents",
      label: "Documents",
      content: <div>Documents content for {patientId}</div>,
    },
  ]

  return (
    <MedicalTabs
      defaultValue={defaultTab}
      tabs={patientTabs}
      variant="underline"
    />
  )
}

export { 
  Tabs, 
  TabsList, 
  TabsTrigger, 
  TabsContent, 
  MedicalTabs,
  PatientTabs 
}