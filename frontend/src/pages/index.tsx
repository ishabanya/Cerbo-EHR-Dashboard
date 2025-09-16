import { MainLayout } from '@/components/layout/main-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useQuery } from '@tanstack/react-query'
import { dashboardApi, appointmentApi } from '@/services/api'
import { 
  Users, 
  Calendar, 
  Activity, 
  DollarSign, 
  TrendingUp,
  Clock,
  UserCheck,
  AlertTriangle
} from 'lucide-react'
import { formatDate, formatDateTime } from '@/lib/utils'
import Link from 'next/link'

export default function Dashboard() {
  // Fetch dashboard data
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardApi.getStats
  })

  const { data: todayOverview, isLoading: todayLoading } = useQuery({
    queryKey: ['today-overview'],
    queryFn: appointmentApi.getTodayOverview
  })

  if (statsLoading || todayLoading) {
    return (
      <MainLayout>
        <div className="space-y-6">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-6">
                  <div className="h-4 bg-gray-200 rounded mb-2"></div>
                  <div className="h-8 bg-gray-200 rounded"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <div className="text-sm text-gray-500">
            {formatDate(new Date(), "long")}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Patients</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats?.total_patients || 0}
                  </p>
                </div>
                <div className="p-3 bg-blue-100 rounded-full">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
              </div>
              <div className="mt-2 flex items-center text-sm">
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-green-600">+12% from last month</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Today's Appointments</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {todayOverview?.total || 0}
                  </p>
                </div>
                <div className="p-3 bg-green-100 rounded-full">
                  <Calendar className="h-6 w-6 text-green-600" />
                </div>
              </div>
              <div className="mt-2 flex items-center text-sm">
                <Clock className="h-4 w-4 text-blue-500 mr-1" />
                <span className="text-gray-600">
                  {todayOverview?.completed || 0} completed
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Providers</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats?.active_providers || 0}
                  </p>
                </div>
                <div className="p-3 bg-purple-100 rounded-full">
                  <UserCheck className="h-6 w-6 text-purple-600" />
                </div>
              </div>
              <div className="mt-2 flex items-center text-sm">
                <Activity className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-green-600">All systems active</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Pending Items</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {(todayOverview?.scheduled || 0) + (todayOverview?.confirmed || 0)}
                  </p>
                </div>
                <div className="p-3 bg-yellow-100 rounded-full">
                  <AlertTriangle className="h-6 w-6 text-yellow-600" />
                </div>
              </div>
              <div className="mt-2 flex items-center text-sm">
                <Clock className="h-4 w-4 text-yellow-500 mr-1" />
                <span className="text-gray-600">Requires attention</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Today's Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Today's Appointments */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Today's Appointments
                <Link href="/appointments">
                  <Button variant="outline" size="sm">
                    View All
                  </Button>
                </Link>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {todayOverview?.appointments?.length > 0 ? (
                <div className="space-y-4">
                  {todayOverview.appointments.slice(0, 5).map((appointment: any) => (
                    <div key={appointment.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium text-sm">
                          {formatDateTime(appointment.appointment_date)}
                        </div>
                        <div className="text-sm text-gray-600">
                          Patient #{appointment.patient_id} - {appointment.appointment_type}
                        </div>
                      </div>
                      <Badge variant={getAppointmentStatusVariant(appointment.status)}>
                        {appointment.status.replace('_', ' ')}
                      </Badge>
                    </div>
                  ))}
                  {todayOverview.appointments.length > 5 && (
                    <div className="text-center">
                      <Link href="/appointments">
                        <Button variant="ghost" size="sm">
                          +{todayOverview.appointments.length - 5} more appointments
                        </Button>
                      </Link>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>No appointments scheduled for today</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <Link href="/patients?action=create">
                  <Button className="w-full h-20 flex flex-col items-center justify-center space-y-2">
                    <Users className="h-6 w-6" />
                    <span>New Patient</span>
                  </Button>
                </Link>
                <Link href="/appointments?action=create">
                  <Button className="w-full h-20 flex flex-col items-center justify-center space-y-2">
                    <Calendar className="h-6 w-6" />
                    <span>Schedule Appointment</span>
                  </Button>
                </Link>
                <Link href="/clinical-records?action=create">
                  <Button variant="outline" className="w-full h-20 flex flex-col items-center justify-center space-y-2">
                    <Activity className="h-6 w-6" />
                    <span>Clinical Note</span>
                  </Button>
                </Link>
                <Link href="/billing?action=create">
                  <Button variant="outline" className="w-full h-20 flex flex-col items-center justify-center space-y-2">
                    <DollarSign className="h-6 w-6" />
                    <span>New Charge</span>
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* System Status */}
        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-100 rounded-full">
                  <Activity className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">API Status</p>
                  <p className="text-sm text-green-600">Online</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-100 rounded-full">
                  <Activity className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">CERBO Integration</p>
                  <p className="text-sm text-green-600">Connected</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-100 rounded-full">
                  <Activity className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Database</p>
                  <p className="text-sm text-green-600">Healthy</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}

function getAppointmentStatusVariant(status: string) {
  switch (status?.toLowerCase()) {
    case 'scheduled':
      return 'scheduled'
    case 'confirmed':
      return 'confirmed'
    case 'cancelled':
      return 'cancelled'
    case 'completed':
      return 'completed'
    case 'in_progress':
    case 'checked_in':
      return 'in-progress'
    default:
      return 'default'
  }
}