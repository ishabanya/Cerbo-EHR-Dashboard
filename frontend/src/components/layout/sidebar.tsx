import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { cn } from '@/lib/utils'
import {
  Calendar,
  Users,
  UserCheck,
  FileText,
  CreditCard,
  Shield,
  BarChart3,
  Home,
  Settings,
  Stethoscope,
  Activity
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Patients', href: '/patients', icon: Users },
  { name: 'Appointments', href: '/appointments', icon: Calendar },
  { name: 'Providers', href: '/providers', icon: UserCheck },
  { name: 'Clinical Records', href: '/clinical-records', icon: FileText },
  { name: 'Billing', href: '/billing', icon: CreditCard },
  { name: 'Insurance', href: '/insurance', icon: Shield },
  { name: 'Reports', href: '/reports', icon: BarChart3 },
]

const secondaryNavigation = [
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const router = useRouter()

  return (
    <div className="flex flex-col w-64 bg-white border-r border-gray-200">
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b border-gray-200">
        <div className="flex items-center">
          <Stethoscope className="h-8 w-8 text-medical-blue" />
          <span className="ml-2 text-xl font-bold text-gray-900">
            EHR Dashboard
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          const isActive = router.pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                isActive
                  ? 'bg-medical-blue text-white'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Secondary Navigation */}
      <div className="px-4 py-4 border-t border-gray-200">
        {secondaryNavigation.map((item) => {
          const isActive = router.pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                isActive
                  ? 'bg-medical-blue text-white'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </div>

      {/* System Status */}
      <div className="px-4 py-4 border-t border-gray-200">
        <div className="flex items-center text-sm text-gray-500">
          <Activity className="h-4 w-4 mr-2 text-green-500" />
          System Online
        </div>
      </div>
    </div>
  )
}