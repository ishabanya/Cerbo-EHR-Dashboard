// Core types for the EHR Dashboard

export interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pages: number
  per_page: number
  has_next: boolean
  has_prev: boolean
}

export interface SearchParams {
  page?: number
  per_page?: number
  search?: string
  sort_by?: string
  sort_order?: "asc" | "desc"
}

// Enums
export enum GenderEnum {
  MALE = "male",
  FEMALE = "female", 
  OTHER = "other",
  UNKNOWN = "unknown"
}

export enum MaritalStatusEnum {
  SINGLE = "single",
  MARRIED = "married",
  DIVORCED = "divorced",
  WIDOWED = "widowed",
  SEPARATED = "separated",
  UNKNOWN = "unknown"
}

export enum AppointmentStatusEnum {
  SCHEDULED = "scheduled",
  CONFIRMED = "confirmed",
  CHECKED_IN = "checked_in",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  CANCELLED = "cancelled",
  NO_SHOW = "no_show",
  RESCHEDULED = "rescheduled"
}

export enum AppointmentTypeEnum {
  CONSULTATION = "consultation",
  FOLLOW_UP = "follow_up",
  PHYSICAL_EXAM = "physical_exam",
  PROCEDURE = "procedure",
  EMERGENCY = "emergency",
  TELEHEALTH = "telehealth",
  VACCINATION = "vaccination",
  LAB_WORK = "lab_work",
  IMAGING = "imaging",
  THERAPY = "therapy"
}

export enum UrgencyEnum {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  URGENT = "urgent"
}

export enum ProviderTypeEnum {
  PHYSICIAN = "physician",
  NURSE_PRACTITIONER = "nurse_practitioner",
  PHYSICIAN_ASSISTANT = "physician_assistant",
  NURSE = "nurse",
  THERAPIST = "therapist",
  TECHNICIAN = "technician",
  SPECIALIST = "specialist",
  CONSULTANT = "consultant"
}

export enum ProviderStatusEnum {
  ACTIVE = "active",
  INACTIVE = "inactive",
  ON_LEAVE = "on_leave",
  RETIRED = "retired"
}

export enum RecordTypeEnum {
  CLINICAL_NOTE = "clinical_note",
  VITAL_SIGNS = "vital_signs",
  LAB_RESULT = "lab_result",
  IMAGING_RESULT = "imaging_result",
  DIAGNOSIS = "diagnosis",
  PRESCRIPTION = "prescription",
  PROCEDURE_NOTE = "procedure_note",
  PROGRESS_NOTE = "progress_note",
  DISCHARGE_SUMMARY = "discharge_summary",
  ALLERGY = "allergy",
  IMMUNIZATION = "immunization"
}

export enum SeverityEnum {
  LOW = "low",
  MODERATE = "moderate",
  HIGH = "high",
  SEVERE = "severe",
  CRITICAL = "critical"
}

export enum StatusEnum {
  ACTIVE = "active",
  INACTIVE = "inactive",
  RESOLVED = "resolved", 
  CHRONIC = "chronic",
  PENDING = "pending"
}

// Patient types
export interface Patient {
  id: number
  first_name: string
  middle_name?: string
  last_name: string
  full_name: string
  date_of_birth: string
  age: number
  gender: GenderEnum
  email?: string
  phone_primary?: string
  phone_secondary?: string
  address_line_1?: string
  address_line_2?: string
  city?: string
  state?: string
  zip_code?: string
  country: string
  marital_status: MaritalStatusEnum
  emergency_contact_name?: string
  emergency_contact_phone?: string
  emergency_contact_relationship?: string
  medical_record_number?: string
  primary_language: string
  is_active: boolean
  created_at: string
  updated_at: string
  notes?: string
  cerbo_patient_id?: string
}

export interface PatientCreate {
  first_name: string
  middle_name?: string
  last_name: string
  date_of_birth: string
  gender: GenderEnum
  email?: string
  phone_primary?: string
  phone_secondary?: string
  address_line_1?: string
  address_line_2?: string
  city?: string
  state?: string
  zip_code?: string
  country?: string
  marital_status?: MaritalStatusEnum
  emergency_contact_name?: string
  emergency_contact_phone?: string
  emergency_contact_relationship?: string
  medical_record_number?: string
  primary_language?: string
  notes?: string
}

export interface PatientUpdate extends Partial<PatientCreate> {
  is_active?: boolean
}

export interface PatientSearch extends SearchParams {
  search_term?: string
  search_type?: "all" | "name" | "phone" | "email" | "mrn" | "dob"
  min_age?: number
  max_age?: number
  gender?: GenderEnum
  state?: string
  is_active?: boolean
}

// Appointment types
export interface Appointment {
  id: number
  patient_id: number
  provider_id: number
  appointment_date: string
  end_time: string
  duration_minutes: number
  appointment_type: AppointmentTypeEnum
  status: AppointmentStatusEnum
  urgency: UrgencyEnum
  chief_complaint?: string
  reason_for_visit?: string
  notes?: string
  room_number?: string
  location?: string
  is_telehealth: boolean
  telehealth_link?: string
  scheduled_by?: string
  check_in_time?: string
  check_out_time?: string
  actual_start_time?: string
  actual_end_time?: string
  estimated_cost?: number
  copay_amount?: number
  created_at: string
  updated_at: string
  cancelled_at?: string
  cancellation_reason?: string
  cerbo_appointment_id?: string
  is_past: boolean
  is_today: boolean
  can_check_in: boolean
}

export interface AppointmentCreate {
  patient_id: number
  provider_id: number
  appointment_date: string
  duration_minutes?: number
  appointment_type: AppointmentTypeEnum
  urgency?: UrgencyEnum
  chief_complaint?: string
  reason_for_visit?: string
  notes?: string
  room_number?: string
  location?: string
  is_telehealth?: boolean
  telehealth_link?: string
  estimated_cost?: number
  copay_amount?: number
}

export interface AppointmentUpdate extends Partial<AppointmentCreate> {
  status?: AppointmentStatusEnum
  cancellation_reason?: string
}

// Provider types
export interface Provider {
  id: number
  first_name: string
  middle_name?: string
  last_name: string
  title?: string
  full_name: string
  display_name: string
  provider_type: ProviderTypeEnum
  license_number?: string
  npi_number?: string
  dea_number?: string
  specialties?: string[]
  primary_specialty: string
  board_certifications?: string[]
  languages_spoken: string[]
  email?: string
  phone_primary?: string
  phone_secondary?: string
  office_address_line_1?: string
  office_address_line_2?: string
  office_city?: string
  office_state?: string
  office_zip_code?: string
  office_phone?: string
  default_appointment_duration: number
  employee_id?: string
  department?: string
  hire_date?: string
  status: ProviderStatusEnum
  is_accepting_new_patients: boolean
  created_at: string
  updated_at: string
  bio?: string
  notes?: string
  cerbo_provider_id?: string
}

export interface ProviderCreate {
  first_name: string
  middle_name?: string
  last_name: string
  title?: string
  provider_type: ProviderTypeEnum
  license_number?: string
  npi_number?: string
  dea_number?: string
  specialties?: string[]
  board_certifications?: string[]
  languages_spoken?: string[]
  email?: string
  phone_primary?: string
  phone_secondary?: string
  office_address_line_1?: string
  office_address_line_2?: string
  office_city?: string
  office_state?: string
  office_zip_code?: string
  office_phone?: string
  default_appointment_duration?: number
  department?: string
  is_accepting_new_patients?: boolean
  bio?: string
  notes?: string
}

export interface ProviderUpdate extends Partial<ProviderCreate> {
  status?: ProviderStatusEnum
}

// Clinical Record types
export interface ClinicalRecord {
  id: number
  patient_id: number
  provider_id: number
  appointment_id?: number
  record_type: RecordTypeEnum
  record_date: string
  title: string
  description?: string
  clinical_notes?: string
  
  // Vital Signs
  temperature?: number
  blood_pressure_systolic?: number
  blood_pressure_diastolic?: number
  blood_pressure?: string
  heart_rate?: number
  respiratory_rate?: number
  oxygen_saturation?: number
  weight?: number
  height?: number
  bmi?: number
  pain_scale?: number
  
  // Lab Results
  lab_test_name?: string
  lab_result_value?: string
  lab_result_unit?: string
  lab_reference_range?: string
  lab_abnormal_flag?: boolean
  
  // Diagnosis
  icd_10_code?: string
  diagnosis_description?: string
  diagnosis_status?: StatusEnum
  diagnosis_severity?: SeverityEnum
  onset_date?: string
  resolution_date?: string
  
  // Prescription
  medication_name?: string
  dosage?: string
  frequency?: string
  duration?: string
  prescribing_instructions?: string
  
  // Procedure
  cpt_code?: string
  procedure_description?: string
  procedure_outcome?: string
  
  // Allergy
  allergen?: string
  allergy_type?: string
  allergy_severity?: SeverityEnum
  allergy_reaction?: string
  
  // Immunization
  vaccine_name?: string
  vaccine_manufacturer?: string
  lot_number?: string
  vaccination_site?: string
  next_due_date?: string
  
  additional_data?: any
  attachments?: string[]
  is_confidential: boolean
  status: StatusEnum
  reviewed_by?: string
  reviewed_at?: string
  created_at: string
  updated_at: string
  cerbo_record_id?: string
  
  // Type indicators
  is_vital_signs: boolean
  is_lab_result: boolean
  is_diagnosis: boolean
  is_prescription: boolean
  is_allergy: boolean
}

export interface ClinicalRecordCreate {
  patient_id: number
  provider_id: number
  appointment_id?: number
  record_type: RecordTypeEnum
  title: string
  description?: string
  clinical_notes?: string
  
  // Optional fields based on record type
  temperature?: number
  blood_pressure_systolic?: number
  blood_pressure_diastolic?: number
  heart_rate?: number
  respiratory_rate?: number
  oxygen_saturation?: number
  weight?: number
  height?: number
  pain_scale?: number
  
  lab_test_name?: string
  lab_result_value?: string
  lab_result_unit?: string
  lab_reference_range?: string
  lab_abnormal_flag?: boolean
  
  icd_10_code?: string
  diagnosis_description?: string
  diagnosis_status?: StatusEnum
  diagnosis_severity?: SeverityEnum
  onset_date?: string
  
  medication_name?: string
  dosage?: string
  frequency?: string
  duration?: string
  prescribing_instructions?: string
  
  cpt_code?: string
  procedure_description?: string
  procedure_outcome?: string
  
  allergen?: string
  allergy_type?: string
  allergy_severity?: SeverityEnum
  allergy_reaction?: string
  
  vaccine_name?: string
  vaccine_manufacturer?: string
  lot_number?: string
  vaccination_site?: string
  next_due_date?: string
  
  additional_data?: any
  is_confidential?: boolean
}

export interface ClinicalRecordUpdate extends Partial<ClinicalRecordCreate> {
  status?: StatusEnum
  reviewed_by?: string
  reviewed_at?: string
}

// Dashboard types
export interface DashboardStats {
  total_patients: number
  active_patients: number
  todays_appointments: number
  pending_appointments: number
  completed_appointments: number
  active_providers: number
  recent_activities: RecentActivity[]
}

export interface RecentActivity {
  id: string
  type: "patient" | "appointment" | "clinical" | "billing"
  description: string
  timestamp: string
  user?: string
}

// Form types
export interface FormField {
  name: string
  label: string
  type: "text" | "email" | "tel" | "date" | "select" | "textarea" | "number"
  required?: boolean
  placeholder?: string
  options?: { value: string; label: string }[]
  validation?: any
}