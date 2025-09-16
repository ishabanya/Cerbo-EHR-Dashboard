import { useState } from 'react'
import { useRouter } from 'next/router'
import { useQuery } from '@tanstack/react-query'
import { MainLayout } from '@/components/layout/main-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { appointmentApi, patientApi, providerApi } from '@/services/api'
import { Appointment } from '@/types'
import { 
  Calendar,
  Plus,
  Clock,
  User,
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  Phone,
  Video
} from 'lucide-react'
import { formatDate, formatDateTime } from '@/lib/utils'
import Link from 'next/link'

export default function AppointmentsPage() {
  const router = useRouter()
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [viewType, setViewType] = useState<'day' | 'week' | 'list'>('day')
  const [statusFilter, setStatusFilter] = useState('all')
  const [providerFilter, setProviderFilter] = useState('all')

  // Format date for API calls
  const dateStr = selectedDate.toISOString().split('T')[0]
  
  // Calculate date range based on view type
  const getDateRange = () => {
    const start = new Date(selectedDate)
    const end = new Date(selectedDate)
    
    if (viewType === 'week') {
      // Start from Monday
      const day = start.getDay()
      const diff = start.getDate() - day + (day === 0 ? -6 : 1)
      start.setDate(diff)
      end.setDate(start.getDate() + 6)
    } else {
      // Same day for day view
      end.setDate(start.getDate())
    }
    
    return {
      start_date: start.toISOString().split('T')[0],
      end_date: end.toISOString().split('T')[0]
    }
  }

  // Fetch appointments
  const { data: appointmentsData, isLoading, error, refetch } = useQuery({
    queryKey: ['appointments', dateStr, viewType, statusFilter, providerFilter],
    queryFn: () => {
      const { start_date, end_date } = getDateRange()
      const params: any = { start_date, end_date }
      
      if (statusFilter !== 'all') {
        params.status = statusFilter
      }
      if (providerFilter !== 'all') {
        params.provider_id = parseInt(providerFilter)
      }
      
      return appointmentApi.getAll(params)
    }
  })

  // Fetch providers for filter
  const { data: providersData } = useQuery({
    queryKey: ['providers-list'],
    queryFn: () => providerApi.getAll({ per_page: 100 })
  })

  // Fetch today's overview
  const { data: todayOverview } = useQuery({
    queryKey: ['today-overview'],
    queryFn: appointmentApi.getTodayOverview
  })

  const navigateDate = (direction: 'prev' | 'next') => {
    const newDate = new Date(selectedDate)
    
    if (viewType === 'day') {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 1 : -1))
    } else if (viewType === 'week') {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7))
    }
    
    setSelectedDate(newDate)
  }

  const getDateRangeDisplay = () => {
    if (viewType === 'day') {
      return formatDate(selectedDate, 'long')
    } else if (viewType === 'week') {
      const { start_date, end_date } = getDateRange()
      return `${formatDate(start_date)} - ${formatDate(end_date)}`
    }
    return formatDate(selectedDate, 'long')
  }

  if (error) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Error loading appointments
            </h3>
            <p className="text-gray-600">Please try again later</p>
            <Button onClick={() => refetch()} className="mt-4">
              Try Again
            </Button>
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
          <h1 className="text-3xl font-bold text-gray-900">Appointments</h1>
          <Link href="/appointments/create">
            <Button className="flex items-center space-x-2">
              <Plus className="h-4 w-4" />
              <span>New Appointment</span>
            </Button>
          </Link>
        </div>

        {/* Today's Stats */}
        {todayOverview && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-gray-900">{todayOverview.total || 0}</div>
                <div className="text-sm text-gray-600">Total Today</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-600">{todayOverview.completed || 0}</div>
                <div className="text-sm text-gray-600">Completed</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-yellow-600">{todayOverview.in_progress || 0}</div>
                <div className="text-sm text-gray-600">In Progress</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">{todayOverview.scheduled || 0}</div>
                <div className="text-sm text-gray-600">Scheduled</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Controls */}
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center space-y-4 lg:space-y-0">
              {/* Date Navigation */}
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => navigateDate('prev')}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  
                  <div className="text-lg font-semibold text-gray-900 min-w-64 text-center">
                    {getDateRangeDisplay()}
                  </div>
                  
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => navigateDate('next')}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>

                <Button
                  variant="outline"
                  onClick={() => setSelectedDate(new Date())}
                  className="text-sm"
                >
                  Today
                </Button>
              </div>

              {/* View Type */}
              <div className="flex items-center space-x-4">
                <div className="flex items-center border rounded-lg">
                  <Button
                    variant={viewType === 'day' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewType('day')}
                    className="rounded-r-none"
                  >
                    Day
                  </Button>
                  <Button
                    variant={viewType === 'week' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewType('week')}
                    className="rounded-none border-x"
                  >
                    Week
                  </Button>
                  <Button
                    variant={viewType === 'list' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewType('list')}
                    className="rounded-l-none"
                  >
                    List
                  </Button>
                </div>
              </div>
            </div>

            {/* Filters */}
            <div className="flex flex-wrap items-center gap-4 mt-4 pt-4 border-t">
              <div className="flex items-center space-x-2">
                <Filter className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-600">Filters:</span>
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="border border-gray-300 rounded px-3 py-1 text-sm focus:ring-2 focus:ring-medical-blue focus:border-transparent"
              >
                <option value="all">All Statuses</option>
                <option value="scheduled">Scheduled</option>
                <option value="confirmed">Confirmed</option>
                <option value="checked_in">Checked In</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>

              <select
                value={providerFilter}
                onChange={(e) => setProviderFilter(e.target.value)}
                className="border border-gray-300 rounded px-3 py-1 text-sm focus:ring-2 focus:ring-medical-blue focus:border-transparent"
              >
                <option value="all">All Providers</option>
                {providersData?.items.map((provider: any) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.display_name}
                  </option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Appointments List */}
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-6">
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-gray-200 rounded"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : appointmentsData?.items.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No appointments found
              </h3>
              <p className="text-gray-600 mb-4">
                No appointments scheduled for the selected date range.
              </p>
              <Link href="/appointments/create">
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Schedule Appointment
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {appointmentsData?.items.map((appointment: Appointment) => (
              <AppointmentCard key={appointment.id} appointment={appointment} />
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  )
}

function AppointmentCard({ appointment }: { appointment: Appointment }) {
  const getStatusVariant = (status: string) => {
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

  const getPriorityVariant = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case 'urgent':
        return 'urgent'
      case 'high':
        return 'high'
      case 'medium':
        return 'medium'
      case 'low':
        return 'low'
      default:
        return 'medium'
    }
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Time Block */}
            <div className="text-center border-r pr-4">
              <div className="text-lg font-semibold text-gray-900">
                {new Date(appointment.appointment_date).toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: true
                })}
              </div>
              <div className="text-sm text-gray-600">
                {appointment.duration_minutes}min
              </div>
            </div>

            {/* Appointment Details */}
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <h3 className="text-lg font-semibold text-gray-900">
                  Patient #{appointment.patient_id}
                </h3>
                <Badge variant={getStatusVariant(appointment.status)}>
                  {appointment.status.replace('_', ' ')}
                </Badge>
                <Badge variant={getPriorityVariant(appointment.urgency)}>
                  {appointment.urgency}
                </Badge>
              </div>
              
              <div className="flex flex-wrap items-center space-x-4 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <User className="h-4 w-4" />
                  <span>Provider #{appointment.provider_id}</span>
                </div>
                
                <div className="flex items-center space-x-1">
                  <Calendar className="h-4 w-4" />
                  <span className="capitalize">
                    {appointment.appointment_type.replace('_', ' ')}
                  </span>
                </div>

                {appointment.is_telehealth && (
                  <div className="flex items-center space-x-1">
                    <Video className="h-4 w-4" />
                    <span>Telehealth</span>
                  </div>
                )}

                {appointment.room_number && (
                  <div className="flex items-center space-x-1">
                    <span>Room {appointment.room_number}</span>
                  </div>
                )}
              </div>

              {appointment.chief_complaint && (
                <div className="mt-2 text-sm text-gray-700">
                  <strong>Chief Complaint:</strong> {appointment.chief_complaint}
                </div>
              )}

              {appointment.reason_for_visit && (
                <div className="mt-1 text-sm text-gray-700">
                  <strong>Reason:</strong> {appointment.reason_for_visit}
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            {appointment.can_check_in && (
              <Button variant="medical" size="sm">
                Check In
              </Button>
            )}
            
            <Link href={`/appointments/${appointment.id}`}>
              <Button variant="outline" size="sm">
                View Details
              </Button>
            </Link>
            
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}