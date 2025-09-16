import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date, format: "short" | "long" | "time" = "short"): string {
  if (!date) return ""
  
  const d = new Date(date)
  
  if (isNaN(d.getTime())) return ""
  
  switch (format) {
    case "long":
      return d.toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric"
      })
    case "time":
      return d.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit"
      })
    default:
      return d.toLocaleDateString("en-US", {
        year: "numeric", 
        month: "short",
        day: "numeric"
      })
  }
}

export function formatDateTime(date: string | Date): string {
  if (!date) return ""
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return ""
  
  return d.toLocaleString("en-US", {
    year: "numeric",
    month: "short", 
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  })
}

export function calculateAge(birthDate: string | Date): number {
  if (!birthDate) return 0
  
  const birth = new Date(birthDate)
  const today = new Date()
  
  if (isNaN(birth.getTime())) return 0
  
  let age = today.getFullYear() - birth.getFullYear()
  const monthDiff = today.getMonth() - birth.getMonth()
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--
  }
  
  return age
}

export function formatCurrency(amount: number): string {
  if (typeof amount !== "number") return "$0.00"
  
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD"
  }).format(amount)
}

export function formatPhoneNumber(phone: string): string {
  if (!phone) return ""
  
  // Remove all non-digit characters
  const digits = phone.replace(/\D/g, "")
  
  // Format as (XXX) XXX-XXXX
  if (digits.length === 10) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`
  }
  
  return phone
}

export function capitalizeFirst(str: string): string {
  if (!str) return ""
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

export function getInitials(firstName: string, lastName: string): string {
  const first = firstName?.charAt(0)?.toUpperCase() || ""
  const last = lastName?.charAt(0)?.toUpperCase() || ""
  return `${first}${last}`
}

export function getStatusColor(status: string): string {
  const statusLower = status?.toLowerCase()
  
  switch (statusLower) {
    case "active":
    case "confirmed":
    case "completed":
    case "paid":
      return "bg-green-100 text-green-800"
    case "scheduled":
    case "pending":
      return "bg-blue-100 text-blue-800"
    case "cancelled":
    case "inactive":
    case "denied":
      return "bg-red-100 text-red-800"
    case "in_progress":
    case "checked_in":
      return "bg-yellow-100 text-yellow-800"
    default:
      return "bg-gray-100 text-gray-800"
  }
}

export function getPriorityColor(priority: string): string {
  const priorityLower = priority?.toLowerCase()
  
  switch (priorityLower) {
    case "high":
    case "urgent":
      return "bg-red-100 text-red-800"
    case "medium":
      return "bg-yellow-100 text-yellow-800"
    case "low":
      return "bg-green-100 text-green-800"
    default:
      return "bg-gray-100 text-gray-800"
  }
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func.apply(null, args), delay)
  }
}

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export function isValidPhone(phone: string): boolean {
  const phoneRegex = /^\d{10}$/
  const digits = phone.replace(/\D/g, "")
  return phoneRegex.test(digits)
}

export function sanitizeInput(input: string): string {
  if (!input) return ""
  
  // Remove potentially dangerous characters
  return input
    .replace(/[<>]/g, "")
    .trim()
}

export function generateId(): string {
  return Math.random().toString(36).substr(2, 9)
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  if (typeof error === "string") return error
  return "An unexpected error occurred"
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes"
  
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

export function isToday(date: string | Date): boolean {
  const d = new Date(date)
  const today = new Date()
  
  return (
    d.getDate() === today.getDate() &&
    d.getMonth() === today.getMonth() &&
    d.getFullYear() === today.getFullYear()
  )
}

export function isOverdue(date: string | Date): boolean {
  const d = new Date(date)
  const today = new Date()
  
  return d < today
}

export function getDaysDifference(date1: string | Date, date2: string | Date): number {
  const d1 = new Date(date1)
  const d2 = new Date(date2)
  
  const diffTime = Math.abs(d2.getTime() - d1.getTime())
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  return diffDays
}