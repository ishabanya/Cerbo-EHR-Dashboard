import { useState } from 'react'
import { useRouter } from 'next/router'
import { useQuery } from '@tanstack/react-query'
import { MainLayout } from '@/components/layout/main-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { patientApi } from '@/services/api'
import { Patient } from '@/types'
import { 
  Search, 
  Plus, 
  Filter,
  MoreHorizontal,
  Phone,
  Mail,
  Calendar,
  MapPin
} from 'lucide-react'
import { formatDate, calculateAge, formatPhoneNumber } from '@/lib/utils'
import Link from 'next/link'

export default function PatientsPage() {
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState('')
  const [searchType, setSearchType] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)
  const [perPage] = useState(20)

  // Fetch patients
  const { data: patientsData, isLoading, error } = useQuery({
    queryKey: ['patients', { 
      page: currentPage, 
      per_page: perPage, 
      search: searchTerm,
      search_type: searchType
    }],
    queryFn: () => patientApi.getAll({
      page: currentPage,
      per_page: perPage,
      search: searchTerm,
      search_type: searchType as any
    }),
    keepPreviousData: true
  })

  const handleSearch = (term: string, type: string = 'all') => {
    setSearchTerm(term)
    setSearchType(type)
    setCurrentPage(1)
  }

  const handleCreatePatient = () => {
    router.push('/patients/create')
  }

  if (error) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Error loading patients
            </h3>
            <p className="text-gray-600">Please try again later</p>
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
          <h1 className="text-3xl font-bold text-gray-900">Patients</h1>
          <Button onClick={handleCreatePatient} className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>New Patient</span>
          </Button>
        </div>

        {/* Search and Filters */}
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Search Input */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search patients by name, phone, email, or MRN..."
                    value={searchTerm}
                    onChange={(e) => handleSearch(e.target.value, searchType)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-medical-blue focus:border-transparent"
                  />
                </div>
              </div>

              {/* Search Type Filter */}
              <div className="flex items-center space-x-2">
                <Filter className="h-4 w-4 text-gray-400" />
                <select
                  value={searchType}
                  onChange={(e) => handleSearch(searchTerm, e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-medical-blue focus:border-transparent"
                >
                  <option value="all">All Fields</option>
                  <option value="name">Name</option>
                  <option value="phone">Phone</option>
                  <option value="email">Email</option>
                  <option value="mrn">MRN</option>
                  <option value="dob">Date of Birth</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results Summary */}
        {patientsData && (
          <div className="text-sm text-gray-600">
            Showing {patientsData.items.length} of {patientsData.total} patients
            {searchTerm && (
              <span> matching "{searchTerm}"</span>
            )}
          </div>
        )}

        {/* Patient List */}
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-6">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gray-200 rounded-full"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : patientsData?.items.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <div className="mb-4">
                <Search className="h-12 w-12 text-gray-300 mx-auto" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {searchTerm ? 'No patients found' : 'No patients yet'}
              </h3>
              <p className="text-gray-600 mb-4">
                {searchTerm 
                  ? `No patients match your search for "${searchTerm}"`
                  : 'Get started by adding your first patient'
                }
              </p>
              {!searchTerm && (
                <Button onClick={handleCreatePatient}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Patient
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Patient Cards */}
            <div className="space-y-4">
              {patientsData?.items.map((patient: Patient) => (
                <PatientCard key={patient.id} patient={patient} />
              ))}
            </div>

            {/* Pagination */}
            {patientsData && patientsData.pages > 1 && (
              <div className="flex justify-center space-x-2">
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={!patientsData.has_prev}
                >
                  Previous
                </Button>
                <span className="flex items-center px-4 py-2 text-sm text-gray-600">
                  Page {currentPage} of {patientsData.pages}
                </span>
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={!patientsData.has_next}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </MainLayout>
  )
}

function PatientCard({ patient }: { patient: Patient }) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Avatar */}
            <div className="w-12 h-12 bg-medical-blue rounded-full flex items-center justify-center text-white font-semibold">
              {patient.first_name.charAt(0)}{patient.last_name.charAt(0)}
            </div>

            {/* Patient Info */}
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-1">
                <h3 className="text-lg font-semibold text-gray-900">
                  {patient.full_name}
                </h3>
                <Badge variant={patient.is_active ? 'active' : 'inactive'}>
                  {patient.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
              
              <div className="flex flex-wrap items-center space-x-4 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <Calendar className="h-4 w-4" />
                  <span>Age {calculateAge(patient.date_of_birth)}</span>
                </div>
                
                {patient.phone_primary && (
                  <div className="flex items-center space-x-1">
                    <Phone className="h-4 w-4" />
                    <span>{formatPhoneNumber(patient.phone_primary)}</span>
                  </div>
                )}
                
                {patient.email && (
                  <div className="flex items-center space-x-1">
                    <Mail className="h-4 w-4" />
                    <span>{patient.email}</span>
                  </div>
                )}

                {patient.city && patient.state && (
                  <div className="flex items-center space-x-1">
                    <MapPin className="h-4 w-4" />
                    <span>{patient.city}, {patient.state}</span>
                  </div>
                )}
              </div>

              {patient.medical_record_number && (
                <div className="mt-1 text-xs text-gray-500">
                  MRN: {patient.medical_record_number}
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            <Link href={`/patients/${patient.id}`}>
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