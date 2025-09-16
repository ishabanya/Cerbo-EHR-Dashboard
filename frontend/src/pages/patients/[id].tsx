import { useRouter } from 'next/router'
import { useQuery } from '@tanstack/react-query'
import { MainLayout } from '@/components/layout/main-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { patientApi, appointmentApi, clinicalRecordApi } from '@/services/api'
import { 
  ArrowLeft, 
  Edit, 
  Phone, 
  Mail, 
  MapPin, 
  Calendar,
  User,
  Heart,
  Pill,
  FileText,
  Clock,
  AlertTriangle
} from 'lucide-react'
import { formatDate, calculateAge, formatPhoneNumber, formatDateTime } from '@/lib/utils'
import Link from 'next/link'

export default function PatientDetailPage() {
  const router = useRouter()
  const { id } = router.query
  const patientId = parseInt(id as string)

  // Fetch patient details
  const { data: patient, isLoading: patientLoading, error } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => patientApi.getById(patientId),
    enabled: !!patientId
  })

  // Fetch patient summary
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['patient-summary', patientId],
    queryFn: () => patientApi.getSummary(patientId),
    enabled: !!patientId
  })

  // Fetch recent appointments
  const { data: recentAppointments } = useQuery({
    queryKey: ['patient-appointments', patientId],
    queryFn: () => appointmentApi.getAll({ patient_id: patientId, per_page: 5 }),
    enabled: !!patientId
  })

  // Fetch allergies
  const { data: allergies } = useQuery({
    queryKey: ['patient-allergies', patientId],
    queryFn: () => clinicalRecordApi.getPatientAllergies(patientId),
    enabled: !!patientId
  })

  // Fetch current medications
  const { data: medications } = useQuery({
    queryKey: ['patient-medications', patientId],
    queryFn: () => clinicalRecordApi.getPatientMedications(patientId),
    enabled: !!patientId
  })

  // Fetch latest vital signs
  const { data: vitalSigns } = useQuery({
    queryKey: ['patient-vital-signs', patientId],
    queryFn: () => clinicalRecordApi.getLatestVitalSigns(patientId),
    enabled: !!patientId
  })

  if (patientLoading) {
    return (
      <MainLayout>
        <div className="space-y-6">
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8 bg-gray-200 rounded animate-pulse"></div>
            <div className="h-8 bg-gray-200 rounded w-48 animate-pulse"></div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
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

  if (error || !patient) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Patient not found
            </h3>
            <p className="text-gray-600 mb-4">
              The patient you're looking for doesn't exist or has been removed.
            </p>
            <Link href="/patients">
              <Button variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Patients
              </Button>
            </Link>
          </div>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/patients">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {patient.full_name}
              </h1>
              <p className="text-gray-600">
                Patient ID: {patient.id} • MRN: {patient.medical_record_number || 'N/A'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={patient.is_active ? 'active' : 'inactive'}>
              {patient.is_active ? 'Active' : 'Inactive'}
            </Badge>
            <Link href={`/patients/${patient.id}/edit`}>
              <Button>
                <Edit className="h-4 w-4 mr-2" />
                Edit Patient
              </Button>
            </Link>
          </div>
        </div>

        {/* Patient Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Demographics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>Demographics</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Date of Birth</label>
                <p className="text-gray-900">
                  {formatDate(patient.date_of_birth)} (Age {calculateAge(patient.date_of_birth)})
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Gender</label>
                <p className="text-gray-900 capitalize">{patient.gender}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Marital Status</label>
                <p className="text-gray-900 capitalize">
                  {patient.marital_status.replace('_', ' ')}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Language</label>
                <p className="text-gray-900">{patient.primary_language}</p>
              </div>
            </CardContent>
          </Card>

          {/* Contact Information */}
          <Card>
            <CardHeader>
              <CardTitle>Contact Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {patient.phone_primary && (
                <div className="flex items-center space-x-2">
                  <Phone className="h-4 w-4 text-gray-400" />
                  <span>{formatPhoneNumber(patient.phone_primary)}</span>
                </div>
              )}
              {patient.phone_secondary && (
                <div className="flex items-center space-x-2">
                  <Phone className="h-4 w-4 text-gray-400" />
                  <span>{formatPhoneNumber(patient.phone_secondary)} (Secondary)</span>
                </div>
              )}
              {patient.email && (
                <div className="flex items-center space-x-2">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <span>{patient.email}</span>
                </div>
              )}
              {(patient.address_line_1 || patient.city) && (
                <div className="flex items-start space-x-2">
                  <MapPin className="h-4 w-4 text-gray-400 mt-0.5" />
                  <div>
                    {patient.address_line_1 && <div>{patient.address_line_1}</div>}
                    {patient.address_line_2 && <div>{patient.address_line_2}</div>}
                    {patient.city && patient.state && (
                      <div>{patient.city}, {patient.state} {patient.zip_code}</div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Emergency Contact */}
          <Card>
            <CardHeader>
              <CardTitle>Emergency Contact</CardTitle>
            </CardHeader>
            <CardContent>
              {patient.emergency_contact_name ? (
                <div className="space-y-2">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Name</label>
                    <p className="text-gray-900">{patient.emergency_contact_name}</p>
                  </div>
                  {patient.emergency_contact_phone && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Phone</label>
                      <p className="text-gray-900">
                        {formatPhoneNumber(patient.emergency_contact_phone)}
                      </p>
                    </div>
                  )}
                  {patient.emergency_contact_relationship && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Relationship</label>
                      <p className="text-gray-900 capitalize">
                        {patient.emergency_contact_relationship}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-gray-500">No emergency contact on file</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Clinical Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Allergies */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5" />
                <span>Allergies</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {allergies && allergies.length > 0 ? (
                <div className="space-y-3">
                  {allergies.map((allergy: any) => (
                    <div key={allergy.id} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{allergy.allergen}</p>
                        <p className="text-sm text-gray-600">
                          {allergy.allergy_type} • {allergy.allergy_severity}
                        </p>
                        {allergy.allergy_reaction && (
                          <p className="text-sm text-gray-600 mt-1">{allergy.allergy_reaction}</p>
                        )}
                      </div>
                      <Badge variant="error">
                        {allergy.allergy_severity}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No known allergies</p>
              )}
            </CardContent>
          </Card>

          {/* Current Medications */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Pill className="h-5 w-5" />
                <span>Current Medications</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {medications && medications.length > 0 ? (
                <div className="space-y-3">
                  {medications.map((medication: any) => (
                    <div key={medication.id} className="p-3 bg-blue-50 rounded-lg">
                      <p className="font-medium text-gray-900">{medication.medication_name}</p>
                      <p className="text-sm text-gray-600">
                        {medication.dosage} • {medication.frequency}
                      </p>
                      {medication.prescribing_instructions && (
                        <p className="text-sm text-gray-600 mt-1">
                          {medication.prescribing_instructions}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No current medications</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Vital Signs */}
        {vitalSigns && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Heart className="h-5 w-5" />
                <span>Latest Vital Signs</span>
                <span className="text-sm font-normal text-gray-500">
                  ({formatDateTime(vitalSigns.record_date)})
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="vitals-grid">
                {vitalSigns.blood_pressure && (
                  <div className="vitals-card">
                    <div className="vitals-value">{vitalSigns.blood_pressure}</div>
                    <div className="vitals-label">Blood Pressure</div>
                  </div>
                )}
                {vitalSigns.heart_rate && (
                  <div className="vitals-card">
                    <div className="vitals-value">
                      {vitalSigns.heart_rate}
                      <span className="vitals-unit">bpm</span>
                    </div>
                    <div className="vitals-label">Heart Rate</div>
                  </div>
                )}
                {vitalSigns.temperature && (
                  <div className="vitals-card">
                    <div className="vitals-value">
                      {vitalSigns.temperature}
                      <span className="vitals-unit">°F</span>
                    </div>
                    <div className="vitals-label">Temperature</div>
                  </div>
                )}
                {vitalSigns.oxygen_saturation && (
                  <div className="vitals-card">
                    <div className="vitals-value">
                      {vitalSigns.oxygen_saturation}
                      <span className="vitals-unit">%</span>
                    </div>
                    <div className="vitals-label">O2 Sat</div>
                  </div>
                )}
                {vitalSigns.weight && (
                  <div className="vitals-card">
                    <div className="vitals-value">
                      {vitalSigns.weight}
                      <span className="vitals-unit">lbs</span>
                    </div>
                    <div className="vitals-label">Weight</div>
                  </div>
                )}
                {vitalSigns.height && (
                  <div className="vitals-card">
                    <div className="vitals-value">
                      {vitalSigns.height}
                      <span className="vitals-unit">in</span>
                    </div>
                    <div className="vitals-label">Height</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent Appointments */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Calendar className="h-5 w-5" />
                <span>Recent Appointments</span>
              </div>
              <Link href={`/appointments?patient_id=${patient.id}`}>
                <Button variant="outline" size="sm">
                  View All
                </Button>
              </Link>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {recentAppointments?.items && recentAppointments.items.length > 0 ? (
              <div className="space-y-3">
                {recentAppointments.items.map((appointment: any) => (
                  <div key={appointment.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Clock className="h-4 w-4 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900">
                          {formatDateTime(appointment.appointment_date)}
                        </p>
                        <p className="text-sm text-gray-600">
                          {appointment.appointment_type.replace('_', ' ')} • {appointment.duration_minutes} min
                        </p>
                      </div>
                    </div>
                    <Badge variant={getAppointmentStatusVariant(appointment.status)}>
                      {appointment.status.replace('_', ' ')}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No recent appointments</p>
            )}
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-center space-x-4">
          <Link href={`/appointments/create?patient_id=${patient.id}`}>
            <Button>
              <Calendar className="h-4 w-4 mr-2" />
              Schedule Appointment
            </Button>
          </Link>
          <Link href={`/clinical-records/create?patient_id=${patient.id}`}>
            <Button variant="outline">
              <FileText className="h-4 w-4 mr-2" />
              Add Clinical Record
            </Button>
          </Link>
        </div>
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