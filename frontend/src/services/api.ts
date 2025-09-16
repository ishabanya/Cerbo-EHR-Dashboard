import axios, { AxiosResponse, AxiosError } from 'axios'
import { toast } from 'react-hot-toast'

// Types
import type {
  Patient,
  PatientCreate,
  PatientUpdate,
  PatientSearch,
  Appointment,
  AppointmentCreate,
  AppointmentUpdate,
  Provider,
  ProviderCreate,
  ProviderUpdate,
  ClinicalRecord,
  ClinicalRecordCreate,
  ClinicalRecordUpdate,
  PaginatedResponse,
  ApiResponse,
  DashboardStats
} from '@/types'

// Create axios instance
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token')
        window.location.href = '/login'
      }
    } else if (error.response?.status === 403) {
      toast.error('Access forbidden')
    } else if (error.response?.status === 404) {
      toast.error('Resource not found')
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.')
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Request timeout. Please try again.')
    } else {
      // Generic error
      const message = error.response?.data?.error || error.message || 'An error occurred'
      toast.error(message)
    }
    
    return Promise.reject(error)
  }
)

// Health check
export const healthApi = {
  check: async (): Promise<any> => {
    const response = await api.get('/api/v1/health')
    return response.data
  },
  
  info: async (): Promise<any> => {
    const response = await api.get('/api/v1/info')
    return response.data
  }
}

// Patient API
export const patientApi = {
  getAll: async (params?: PatientSearch): Promise<PaginatedResponse<Patient>> => {
    const response = await api.get('/api/v1/patients', { params })
    return response.data
  },
  
  getById: async (id: number): Promise<Patient> => {
    const response = await api.get(`/api/v1/patients/${id}`)
    return response.data
  },
  
  create: async (data: PatientCreate): Promise<Patient> => {
    const response = await api.post('/api/v1/patients', data)
    return response.data
  },
  
  update: async (id: number, data: PatientUpdate): Promise<Patient> => {
    const response = await api.put(`/api/v1/patients/${id}`, data)
    return response.data
  },
  
  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/patients/${id}`)
  },
  
  search: async (params: PatientSearch): Promise<Patient[]> => {
    const response = await api.get('/api/v1/patients/search', { params })
    return response.data
  },
  
  getByMrn: async (mrn: string): Promise<Patient> => {
    const response = await api.get(`/api/v1/patients/mrn/${mrn}`)
    return response.data
  },
  
  getSummary: async (id: number): Promise<any> => {
    const response = await api.get(`/api/v1/patients/${id}/summary`)
    return response.data
  },
  
  reactivate: async (id: number): Promise<Patient> => {
    const response = await api.post(`/api/v1/patients/${id}/reactivate`)
    return response.data
  }
}

// Appointment API
export const appointmentApi = {
  getAll: async (params?: any): Promise<PaginatedResponse<Appointment>> => {
    const response = await api.get('/api/v1/appointments', { params })
    return response.data
  },
  
  getById: async (id: number): Promise<Appointment> => {
    const response = await api.get(`/api/v1/appointments/${id}`)
    return response.data
  },
  
  create: async (data: AppointmentCreate): Promise<Appointment> => {
    const response = await api.post('/api/v1/appointments', data)
    return response.data
  },
  
  update: async (id: number, data: AppointmentUpdate): Promise<Appointment> => {
    const response = await api.put(`/api/v1/appointments/${id}`, data)
    return response.data
  },
  
  cancel: async (id: number, reason?: string): Promise<void> => {
    await api.delete(`/api/v1/appointments/${id}`, { 
      params: { reason } 
    })
  },
  
  checkConflicts: async (data: {
    provider_id: number
    appointment_date: string
    duration_minutes?: number
    exclude_appointment_id?: number
  }): Promise<{ has_conflicts: boolean; conflicts: Appointment[] }> => {
    const response = await api.post('/api/v1/appointments/check-conflicts', data)
    return response.data
  },
  
  getProviderAvailability: async (
    providerId: number, 
    startDate: string, 
    endDate: string
  ): Promise<any> => {
    const response = await api.get(`/api/v1/appointments/provider/${providerId}/availability`, {
      params: { start_date: startDate, end_date: endDate }
    })
    return response.data
  },
  
  checkIn: async (id: number): Promise<Appointment> => {
    const response = await api.post(`/api/v1/appointments/${id}/check-in`)
    return response.data
  },
  
  start: async (id: number): Promise<Appointment> => {
    const response = await api.post(`/api/v1/appointments/${id}/start`)
    return response.data
  },
  
  complete: async (id: number, notes?: string): Promise<Appointment> => {
    const response = await api.post(`/api/v1/appointments/${id}/complete`, 
      null, { params: { notes } }
    )
    return response.data
  },
  
  markNoShow: async (id: number): Promise<Appointment> => {
    const response = await api.post(`/api/v1/appointments/${id}/no-show`)
    return response.data
  },
  
  getTodayOverview: async (): Promise<any> => {
    const response = await api.get('/api/v1/appointments/today/overview')
    return response.data
  }
}

// Provider API
export const providerApi = {
  getAll: async (params?: any): Promise<PaginatedResponse<Provider>> => {
    const response = await api.get('/api/v1/providers', { params })
    return response.data
  },
  
  getById: async (id: number): Promise<Provider> => {
    const response = await api.get(`/api/v1/providers/${id}`)
    return response.data
  },
  
  create: async (data: ProviderCreate): Promise<Provider> => {
    const response = await api.post('/api/v1/providers', data)
    return response.data
  },
  
  update: async (id: number, data: ProviderUpdate): Promise<Provider> => {
    const response = await api.put(`/api/v1/providers/${id}`, data)
    return response.data
  },
  
  getBySpecialty: async (specialty: string): Promise<Provider[]> => {
    const response = await api.get(`/api/v1/providers/specialty/${specialty}`)
    return response.data
  },
  
  getSchedule: async (
    id: number, 
    startDate: string, 
    endDate: string
  ): Promise<any> => {
    const response = await api.get(`/api/v1/providers/${id}/schedule`, {
      params: { start_date: startDate, end_date: endDate }
    })
    return response.data
  },
  
  getAvailability: async (
    id: number, 
    startDate: string, 
    endDate: string
  ): Promise<any> => {
    const response = await api.get(`/api/v1/providers/${id}/availability`, {
      params: { start_date: startDate, end_date: endDate }
    })
    return response.data
  },
  
  getWorkload: async (
    id: number, 
    startDate: string, 
    endDate: string
  ): Promise<any> => {
    const response = await api.get(`/api/v1/providers/${id}/workload`, {
      params: { start_date: startDate, end_date: endDate }
    })
    return response.data
  }
}

// Clinical Records API
export const clinicalRecordApi = {
  getAll: async (params?: any): Promise<PaginatedResponse<ClinicalRecord>> => {
    const response = await api.get('/api/v1/clinical-records', { params })
    return response.data
  },
  
  getById: async (id: number): Promise<ClinicalRecord> => {
    const response = await api.get(`/api/v1/clinical-records/${id}`)
    return response.data
  },
  
  create: async (data: ClinicalRecordCreate): Promise<ClinicalRecord> => {
    const response = await api.post('/api/v1/clinical-records', data)
    return response.data
  },
  
  update: async (id: number, data: ClinicalRecordUpdate): Promise<ClinicalRecord> => {
    const response = await api.put(`/api/v1/clinical-records/${id}`, data)
    return response.data
  },
  
  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/clinical-records/${id}`)
  },
  
  getPatientHistory: async (patientId: number): Promise<ClinicalRecord[]> => {
    const response = await api.get(`/api/v1/clinical-records/patient/${patientId}/history`)
    return response.data
  },
  
  getPatientTimeline: async (patientId: number): Promise<any> => {
    const response = await api.get(`/api/v1/clinical-records/patient/${patientId}/timeline`)
    return response.data
  },
  
  getByType: async (recordType: string): Promise<ClinicalRecord[]> => {
    const response = await api.get(`/api/v1/clinical-records/type/${recordType}`)
    return response.data
  },
  
  createVitalSigns: async (data: any): Promise<ClinicalRecord> => {
    const response = await api.post('/api/v1/clinical-records/vital-signs', data)
    return response.data
  },
  
  createDiagnosis: async (data: any): Promise<ClinicalRecord> => {
    const response = await api.post('/api/v1/clinical-records/diagnosis', data)
    return response.data
  },
  
  createPrescription: async (data: any): Promise<ClinicalRecord> => {
    const response = await api.post('/api/v1/clinical-records/prescription', data)
    return response.data
  },
  
  getPatientAllergies: async (patientId: number): Promise<ClinicalRecord[]> => {
    const response = await api.get(`/api/v1/clinical-records/patient/${patientId}/allergies`)
    return response.data
  },
  
  getPatientMedications: async (patientId: number): Promise<ClinicalRecord[]> => {
    const response = await api.get(`/api/v1/clinical-records/patient/${patientId}/medications`)
    return response.data
  },
  
  getPatientDiagnoses: async (patientId: number): Promise<ClinicalRecord[]> => {
    const response = await api.get(`/api/v1/clinical-records/patient/${patientId}/diagnoses`)
    return response.data
  },
  
  getLatestVitalSigns: async (patientId: number): Promise<ClinicalRecord | null> => {
    const response = await api.get(`/api/v1/clinical-records/patient/${patientId}/vital-signs/latest`)
    return response.data
  },
  
  markAsReviewed: async (id: number): Promise<ClinicalRecord> => {
    const response = await api.post(`/api/v1/clinical-records/${id}/review`)
    return response.data
  },
  
  getSummaryStats: async (): Promise<any> => {
    const response = await api.get('/api/v1/clinical-records/stats/summary')
    return response.data
  }
}

// Dashboard API (would be implemented as needed)
export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    // This would combine data from multiple endpoints
    // For now, return mock data structure
    const [patientsResp, appointmentsResp, providersResp] = await Promise.all([
      patientApi.getAll({ per_page: 1 }),
      appointmentApi.getTodayOverview(),
      providerApi.getAll({ per_page: 1, status: 'active' })
    ])
    
    return {
      total_patients: patientsResp.total,
      active_patients: patientsResp.total, // Would filter by active
      todays_appointments: appointmentsResp.total || 0,
      pending_appointments: appointmentsResp.scheduled || 0,
      completed_appointments: appointmentsResp.completed || 0,
      active_providers: providersResp.total,
      recent_activities: [] // Would implement activity tracking
    }
  }
}

export default api