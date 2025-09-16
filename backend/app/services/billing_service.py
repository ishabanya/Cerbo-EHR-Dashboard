from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc, asc
from datetime import datetime, date, timedelta
import logging
from decimal import Decimal

from .base_repository import BaseRepository
from ..models.billing import Billing, BillingStatusEnum, TransactionTypeEnum, PaymentMethodEnum
from ..models.patient import Patient
from ..models.appointment import Appointment
from ..models.insurance import Insurance
from ..api.cerbo_client import CerboClient, CerboAPIException

logger = logging.getLogger(__name__)

class BillingService(BaseRepository[Billing]):
    """
    Billing service with payment processing, balance calculation, and CERBO API integration
    """
    
    def __init__(self, db: Session, cerbo_client: CerboClient = None):
        super().__init__(Billing, db)
        self.cerbo_client = cerbo_client
    
    def search_billing(
        self, 
        search_term: str, 
        search_type: str = "all",
        skip: int = 0, 
        limit: int = 100
    ) -> List[Billing]:
        """
        Advanced billing search with multiple criteria
        """
        try:
            if not search_term:
                return self.get_all(skip=skip, limit=limit, order_by="service_date", order_direction="desc")
            
            query = self.db.query(Billing).join(Patient)
            
            if search_type == "patient":
                # Search by patient name
                query = query.filter(
                    or_(
                        Patient.first_name.ilike(f"%{search_term}%"),
                        Patient.last_name.ilike(f"%{search_term}%"),
                        func.concat(Patient.first_name, ' ', Patient.last_name).ilike(f"%{search_term}%"),
                        Patient.medical_record_number.ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "invoice":
                # Search by invoice number
                query = query.filter(Billing.invoice_number.ilike(f"%{search_term}%"))
            elif search_type == "claim":
                # Search by claim number
                query = query.filter(Billing.claim_number.ilike(f"%{search_term}%"))
            elif search_type == "procedure":
                # Search by procedure code or description
                query = query.filter(
                    or_(
                        Billing.procedure_code.ilike(f"%{search_term}%"),
                        Billing.procedure_description.ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "diagnosis":
                # Search by diagnosis code or description
                query = query.filter(
                    or_(
                        Billing.diagnosis_code.ilike(f"%{search_term}%"),
                        Billing.diagnosis_description.ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "provider":
                # Search by provider name
                query = query.filter(
                    or_(
                        Billing.rendering_provider.ilike(f"%{search_term}%"),
                        Billing.referring_provider.ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "status":
                # Search by billing status
                try:
                    status = BillingStatusEnum(search_term.lower())
                    query = query.filter(Billing.status == status)
                except ValueError:
                    logger.warning(f"Invalid billing status for search: {search_term}")
                    return []
            elif search_type == "amount":
                # Search by amount (exact match or range)
                try:
                    amount = float(search_term)
                    query = query.filter(
                        or_(
                            Billing.charge_amount == amount,
                            Billing.paid_amount == amount,
                            Billing.balance_amount == amount
                        )
                    )
                except ValueError:
                    logger.warning(f"Invalid amount for search: {search_term}")
                    return []
            else:
                # Search all text fields
                query = query.filter(
                    or_(
                        Billing.invoice_number.ilike(f"%{search_term}%"),
                        Billing.claim_number.ilike(f"%{search_term}%"),
                        Billing.procedure_code.ilike(f"%{search_term}%"),
                        Billing.procedure_description.ilike(f"%{search_term}%"),
                        Billing.diagnosis_code.ilike(f"%{search_term}%"),
                        Billing.diagnosis_description.ilike(f"%{search_term}%"),
                        Billing.rendering_provider.ilike(f"%{search_term}%"),
                        Billing.referring_provider.ilike(f"%{search_term}%"),
                        Billing.notes.ilike(f"%{search_term}%"),
                        Patient.first_name.ilike(f"%{search_term}%"),
                        Patient.last_name.ilike(f"%{search_term}%")
                    )
                )
            
            return query.order_by(desc(Billing.service_date)).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error searching billing records: {e}")
            raise
    
    def get_patient_billing(
        self, 
        patient_id: int, 
        skip: int = 0, 
        limit: int = 100,
        status: BillingStatusEnum = None
    ) -> List[Billing]:
        """Get billing records for a specific patient"""
        try:
            query = self.db.query(Billing).filter(Billing.patient_id == patient_id)
            
            if status:
                query = query.filter(Billing.status == status)
            
            return query.order_by(desc(Billing.service_date)).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error getting billing for patient {patient_id}: {e}")
            raise
    
    def get_appointment_billing(self, appointment_id: int) -> List[Billing]:
        """Get billing records for a specific appointment"""
        try:
            return self.db.query(Billing).filter(
                Billing.appointment_id == appointment_id
            ).order_by(desc(Billing.service_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting billing for appointment {appointment_id}: {e}")
            raise
    
    def get_outstanding_balances(
        self, 
        patient_id: int = None,
        days_outstanding: int = None
    ) -> List[Billing]:
        """Get billing records with outstanding balances"""
        try:
            query = self.db.query(Billing).filter(Billing.balance_amount > 0)
            
            if patient_id:
                query = query.filter(Billing.patient_id == patient_id)
            
            if days_outstanding:
                cutoff_date = datetime.utcnow() - timedelta(days=days_outstanding)
                query = query.filter(Billing.service_date <= cutoff_date)
            
            return query.order_by(desc(Billing.service_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting outstanding balances: {e}")
            raise
    
    def get_overdue_accounts(self, days_overdue: int = 30) -> List[Billing]:
        """Get overdue billing accounts"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_overdue)
            
            return self.db.query(Billing).filter(
                and_(
                    Billing.balance_amount > 0,
                    Billing.service_date <= cutoff_date,
                    Billing.status.in_([
                        BillingStatusEnum.PENDING,
                        BillingStatusEnum.PARTIALLY_PAID,
                        BillingStatusEnum.SUBMITTED
                    ])
                )
            ).order_by(desc(Billing.service_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting overdue accounts: {e}")
            raise
    
    def get_billing_by_date_range(
        self, 
        start_date: date, 
        end_date: date,
        patient_id: int = None,
        status: BillingStatusEnum = None
    ) -> List[Billing]:
        """Get billing records within a date range"""
        try:
            query = self.db.query(Billing).filter(
                and_(
                    func.date(Billing.service_date) >= start_date,
                    func.date(Billing.service_date) <= end_date
                )
            )
            
            if patient_id:
                query = query.filter(Billing.patient_id == patient_id)
            
            if status:
                query = query.filter(Billing.status == status)
            
            return query.order_by(desc(Billing.service_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting billing by date range: {e}")
            raise
    
    def create_charge(self, charge_data: Dict[str, Any]) -> Billing:
        """Create a new billing charge"""
        try:
            # Ensure this is a charge transaction
            charge_data["transaction_type"] = TransactionTypeEnum.CHARGE
            charge_data["status"] = charge_data.get("status", BillingStatusEnum.DRAFT)
            
            # Set balance equal to charge amount initially
            charge_amount = float(charge_data.get("charge_amount", 0))
            charge_data["balance_amount"] = charge_amount
            
            # Generate invoice number if not provided
            if not charge_data.get("invoice_number"):
                charge_data["invoice_number"] = self._generate_invoice_number()
            
            billing = self.create(charge_data)
            logger.info(f"Created billing charge {billing.id} for ${charge_amount}")
            
            return billing
            
        except Exception as e:
            logger.error(f"Error creating billing charge: {e}")
            raise
    
    def process_payment(
        self, 
        billing_id: int, 
        payment_amount: float, 
        payment_method: PaymentMethodEnum,
        payment_reference: str = None
    ) -> Optional[Billing]:
        """Process a payment against a billing record"""
        try:
            billing = self.get_by_id(billing_id)
            if not billing:
                return None
            
            if payment_amount <= 0:
                raise ValueError("Payment amount must be greater than 0")
            
            if payment_amount > billing.balance_amount:
                raise ValueError(f"Payment amount ${payment_amount} exceeds balance ${billing.balance_amount}")
            
            # Add payment
            billing.add_payment(payment_amount, payment_method, payment_reference)
            
            # Commit changes
            self.db.commit()
            self.db.refresh(billing)
            
            logger.info(f"Processed payment of ${payment_amount} for billing {billing_id}")
            
            return billing
            
        except Exception as e:
            logger.error(f"Error processing payment for billing {billing_id}: {e}")
            raise
    
    def process_insurance_payment(
        self, 
        billing_id: int, 
        payment_amount: float, 
        is_primary: bool = True,
        payment_reference: str = None
    ) -> Optional[Billing]:
        """Process an insurance payment"""
        try:
            billing = self.get_by_id(billing_id)
            if not billing:
                return None
            
            if payment_amount <= 0:
                raise ValueError("Payment amount must be greater than 0")
            
            # Add insurance payment
            billing.add_insurance_payment(payment_amount, is_primary)
            
            # Add note about insurance payment
            insurance_type = "Primary" if is_primary else "Secondary"
            note = f"{insurance_type} insurance payment: ${payment_amount}"
            if payment_reference:
                note += f" (Ref: {payment_reference})"
            
            current_notes = billing.notes or ""
            billing.notes = f"{current_notes}\n{note}".strip()
            
            # Commit changes
            self.db.commit()
            self.db.refresh(billing)
            
            logger.info(f"Processed {insurance_type.lower()} insurance payment of ${payment_amount} for billing {billing_id}")
            
            return billing
            
        except Exception as e:
            logger.error(f"Error processing insurance payment for billing {billing_id}: {e}")
            raise
    
    def process_adjustment(
        self, 
        billing_id: int, 
        adjustment_amount: float, 
        reason: str
    ) -> Optional[Billing]:
        """Process an adjustment (write-off, discount, etc.)"""
        try:
            billing = self.get_by_id(billing_id)
            if not billing:
                return None
            
            if adjustment_amount <= 0:
                raise ValueError("Adjustment amount must be greater than 0")
            
            # Add adjustment
            billing.add_adjustment(adjustment_amount, reason)
            
            # Commit changes
            self.db.commit()
            self.db.refresh(billing)
            
            logger.info(f"Processed adjustment of ${adjustment_amount} for billing {billing_id}: {reason}")
            
            return billing
            
        except Exception as e:
            logger.error(f"Error processing adjustment for billing {billing_id}: {e}")
            raise
    
    def calculate_patient_balance(self, patient_id: int) -> Dict[str, Any]:
        """Calculate total patient balance across all billing records"""
        try:
            billing_records = self.get_patient_billing(patient_id)
            
            total_charges = sum(float(b.charge_amount) for b in billing_records)
            total_payments = sum(float(b.paid_amount) for b in billing_records)
            total_insurance = sum(float(b.primary_insurance_paid + b.secondary_insurance_paid) for b in billing_records)
            total_adjustments = sum(float(b.adjustment_amount) for b in billing_records)
            total_balance = sum(float(b.balance_amount) for b in billing_records)
            
            # Get overdue balance (older than 30 days)
            overdue_records = [b for b in billing_records if b.is_overdue]
            overdue_balance = sum(float(b.balance_amount) for b in overdue_records)
            
            # Count by status
            status_counts = {}
            for status in BillingStatusEnum:
                status_counts[status.value] = len([b for b in billing_records if b.status == status])
            
            return {
                "patient_id": patient_id,
                "totals": {
                    "total_charges": round(total_charges, 2),
                    "total_payments": round(total_payments, 2),
                    "total_insurance_payments": round(total_insurance, 2),
                    "total_adjustments": round(total_adjustments, 2),
                    "current_balance": round(total_balance, 2),
                    "overdue_balance": round(overdue_balance, 2)
                },
                "statistics": {
                    "total_billing_records": len(billing_records),
                    "paid_in_full_count": len([b for b in billing_records if b.is_paid_in_full]),
                    "overdue_count": len(overdue_records),
                    "average_charge_amount": round(total_charges / len(billing_records), 2) if billing_records else 0
                },
                "by_status": status_counts,
                "payment_breakdown": {
                    "patient_payments": round(total_payments, 2),
                    "primary_insurance": round(sum(float(b.primary_insurance_paid) for b in billing_records), 2),
                    "secondary_insurance": round(sum(float(b.secondary_insurance_paid) for b in billing_records), 2),
                    "adjustments": round(total_adjustments, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating patient balance for {patient_id}: {e}")
            raise
    
    def estimate_patient_cost(
        self, 
        patient_id: int, 
        procedure_code: str, 
        estimated_charge: float
    ) -> Dict[str, Any]:
        """Estimate patient cost for a procedure using insurance information"""
        try:
            # Get patient's primary insurance
            from .insurance_service import InsuranceService
            insurance_service = InsuranceService(self.db, self.cerbo_client)
            primary_insurance = insurance_service.get_primary_insurance(patient_id)
            
            if not primary_insurance:
                return {
                    "estimated_charge": estimated_charge,
                    "patient_responsibility": estimated_charge,
                    "insurance_coverage": 0,
                    "message": "No active primary insurance found"
                }
            
            # Calculate cost using insurance service
            cost_breakdown = insurance_service.calculate_patient_cost(
                primary_insurance.id, estimated_charge, "general", procedure_code
            )
            
            # Add additional context
            cost_breakdown.update({
                "procedure_code": procedure_code,
                "estimated_charge": estimated_charge,
                "insurance_company": primary_insurance.insurance_company,
                "insurance_plan": primary_insurance.insurance_plan_name
            })
            
            return cost_breakdown
            
        except Exception as e:
            logger.error(f"Error estimating patient cost: {e}")
            raise
    
    def get_aging_report(self, as_of_date: date = None) -> Dict[str, Any]:
        """Generate accounts receivable aging report"""
        try:
            if not as_of_date:
                as_of_date = date.today()
            
            # Get all outstanding balances
            outstanding = self.get_outstanding_balances()
            
            # Define aging buckets
            aging_buckets = {
                "current": [],      # 0-30 days
                "30_60": [],        # 31-60 days
                "61_90": [],        # 61-90 days
                "91_120": [],       # 91-120 days
                "over_120": []      # Over 120 days
            }
            
            for billing in outstanding:
                days_outstanding = (as_of_date - billing.service_date.date()).days
                balance = float(billing.balance_amount)
                
                if days_outstanding <= 30:
                    aging_buckets["current"].append(billing)
                elif days_outstanding <= 60:
                    aging_buckets["30_60"].append(billing)
                elif days_outstanding <= 90:
                    aging_buckets["61_90"].append(billing)
                elif days_outstanding <= 120:
                    aging_buckets["91_120"].append(billing)
                else:
                    aging_buckets["over_120"].append(billing)
            
            # Calculate totals for each bucket
            aging_summary = {}
            total_outstanding = 0
            
            for bucket, records in aging_buckets.items():
                bucket_total = sum(float(b.balance_amount) for b in records)
                aging_summary[bucket] = {
                    "count": len(records),
                    "total_amount": round(bucket_total, 2)
                }
                total_outstanding += bucket_total
            
            # Calculate percentages
            for bucket in aging_summary:
                if total_outstanding > 0:
                    aging_summary[bucket]["percentage"] = round(
                        (aging_summary[bucket]["total_amount"] / total_outstanding) * 100, 2
                    )
                else:
                    aging_summary[bucket]["percentage"] = 0
            
            return {
                "as_of_date": as_of_date.isoformat(),
                "total_outstanding": round(total_outstanding, 2),
                "total_accounts": len(outstanding),
                "aging_buckets": aging_summary,
                "details": {
                    "current": [b.to_dict() for b in aging_buckets["current"][:10]],      # Top 10
                    "30_60": [b.to_dict() for b in aging_buckets["30_60"][:10]],
                    "61_90": [b.to_dict() for b in aging_buckets["61_90"][:10]],
                    "91_120": [b.to_dict() for b in aging_buckets["91_120"][:10]],
                    "over_120": [b.to_dict() for b in aging_buckets["over_120"][:10]]
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating aging report: {e}")
            raise
    
    def get_billing_statistics(
        self, 
        start_date: date = None, 
        end_date: date = None
    ) -> Dict[str, Any]:
        """Get billing statistics for a date range"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            billing_records = self.get_billing_by_date_range(start_date, end_date)
            
            # Calculate totals
            total_charges = sum(float(b.charge_amount) for b in billing_records)
            total_payments = sum(float(b.paid_amount) for b in billing_records)
            total_insurance = sum(float(b.primary_insurance_paid + b.secondary_insurance_paid) for b in billing_records)
            total_adjustments = sum(float(b.adjustment_amount) for b in billing_records)
            total_balance = sum(float(b.balance_amount) for b in billing_records)
            
            # Collection rate
            collection_rate = 0
            if total_charges > 0:
                collection_rate = ((total_payments + total_insurance) / total_charges) * 100
            
            # Count by status
            status_counts = {}
            for status in BillingStatusEnum:
                status_counts[status.value] = len([b for b in billing_records if b.status == status])
            
            # Count by transaction type
            type_counts = {}
            for trans_type in TransactionTypeEnum:
                type_counts[trans_type.value] = len([b for b in billing_records if b.transaction_type == trans_type])
            
            # Top procedure codes
            procedure_counts = {}
            for billing in billing_records:
                if billing.procedure_code:
                    procedure_counts[billing.procedure_code] = procedure_counts.get(billing.procedure_code, 0) + 1
            
            top_procedures = sorted(procedure_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days + 1
                },
                "totals": {
                    "total_charges": round(total_charges, 2),
                    "total_payments": round(total_payments, 2),
                    "total_insurance_payments": round(total_insurance, 2),
                    "total_adjustments": round(total_adjustments, 2),
                    "outstanding_balance": round(total_balance, 2),
                    "collection_rate_percentage": round(collection_rate, 2)
                },
                "record_counts": {
                    "total_billing_records": len(billing_records),
                    "unique_patients": len(set(b.patient_id for b in billing_records)),
                    "paid_in_full": len([b for b in billing_records if b.is_paid_in_full]),
                    "overdue": len([b for b in billing_records if b.is_overdue])
                },
                "by_status": status_counts,
                "by_transaction_type": type_counts,
                "top_procedures": [{"code": code, "count": count} for code, count in top_procedures],
                "daily_averages": {
                    "charges_per_day": round(total_charges / ((end_date - start_date).days + 1), 2),
                    "payments_per_day": round((total_payments + total_insurance) / ((end_date - start_date).days + 1), 2),
                    "records_per_day": round(len(billing_records) / ((end_date - start_date).days + 1), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting billing statistics: {e}")
            raise
    
    def get_by_cerbo_id(self, cerbo_id: str) -> Optional[Billing]:
        """Get billing record by CERBO external ID"""
        return self.get_by_field("cerbo_billing_id", cerbo_id)
    
    async def create_billing_with_cerbo_sync(self, billing_data: Dict[str, Any]) -> Billing:
        """Create billing record locally and sync with CERBO API"""
        try:
            # Create billing locally first
            billing = self.create_charge(billing_data)
            
            # Sync with CERBO if client is available
            if self.cerbo_client:
                try:
                    cerbo_billing_data = self._convert_to_cerbo_format(billing)
                    cerbo_response = await self.cerbo_client.create_charge(cerbo_billing_data)
                    
                    # Update local billing with CERBO ID
                    if cerbo_response and 'id' in cerbo_response:
                        self.update(billing.id, {"cerbo_billing_id": cerbo_response['id']})
                        logger.info(f"Billing {billing.id} synced with CERBO ID: {cerbo_response['id']}")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync billing {billing.id} with CERBO: {e}")
                    # Continue without CERBO sync
            
            return billing
        except Exception as e:
            logger.error(f"Error creating billing with CERBO sync: {e}")
            raise
    
    async def process_payment_with_cerbo_sync(
        self, 
        billing_id: int, 
        payment_data: Dict[str, Any]
    ) -> Optional[Billing]:
        """Process payment locally and sync with CERBO API"""
        try:
            payment_amount = payment_data.get("amount")
            payment_method = PaymentMethodEnum(payment_data.get("method", "cash"))
            payment_reference = payment_data.get("reference")
            
            # Process payment locally
            billing = self.process_payment(billing_id, payment_amount, payment_method, payment_reference)
            if not billing:
                return None
            
            # Sync with CERBO if client is available
            if self.cerbo_client and billing.cerbo_billing_id:
                try:
                    cerbo_payment_data = {
                        "billing_id": billing.cerbo_billing_id,
                        "amount": payment_amount,
                        "method": payment_method.value,
                        "reference": payment_reference,
                        "date": datetime.utcnow().isoformat()
                    }
                    await self.cerbo_client.process_payment(cerbo_payment_data)
                    logger.info(f"Payment for billing {billing.id} synced with CERBO")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync payment for billing {billing.id} with CERBO: {e}")
                    # Continue without CERBO sync
            
            return billing
        except Exception as e:
            logger.error(f"Error processing payment with CERBO sync: {e}")
            raise
    
    async def sync_from_cerbo(self, cerbo_billing_id: str, patient_id: int) -> Optional[Billing]:
        """Sync billing data from CERBO API"""
        if not self.cerbo_client:
            raise ValueError("CERBO client not available")
        
        try:
            # Get patient's CERBO ID
            patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient or not patient.cerbo_patient_id:
                raise ValueError(f"Patient {patient_id} not found or missing CERBO ID")
            
            # Get billing data from CERBO
            cerbo_billing = await self.cerbo_client.get_patient_billing(patient.cerbo_patient_id)
            
            if not cerbo_billing:
                return None
            
            # Find the specific billing record
            billing_record = None
            if isinstance(cerbo_billing, list):
                billing_record = next((bill for bill in cerbo_billing if bill.get('id') == cerbo_billing_id), None)
            elif cerbo_billing.get('id') == cerbo_billing_id:
                billing_record = cerbo_billing
            
            if not billing_record:
                return None
            
            # Check if billing already exists locally
            existing_billing = self.get_by_cerbo_id(cerbo_billing_id)
            
            # Convert CERBO data to local format
            billing_data = self._convert_from_cerbo_format(billing_record)
            billing_data['cerbo_billing_id'] = cerbo_billing_id
            billing_data['patient_id'] = patient_id
            
            if existing_billing:
                # Update existing billing
                return self.update(existing_billing.id, billing_data)
            else:
                # Create new billing
                return self.create(billing_data)
                
        except CerboAPIException as e:
            logger.error(f"Error syncing billing from CERBO: {e}")
            raise
    
    def _generate_invoice_number(self) -> str:
        """Generate a unique invoice number"""
        # Simple implementation - in production, this would be more sophisticated
        import uuid
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"INV-{timestamp}-{unique_id}"
    
    def _convert_to_cerbo_format(self, billing: Billing) -> Dict[str, Any]:
        """Convert local billing model to CERBO API format"""
        return {
            "patient_id": billing.patient.cerbo_patient_id if billing.patient else None,
            "service_date": billing.service_date.isoformat() if billing.service_date else None,
            "procedure_code": billing.procedure_code,
            "procedure_description": billing.procedure_description,
            "diagnosis_code": billing.diagnosis_code,
            "diagnosis_description": billing.diagnosis_description,
            "charge_amount": float(billing.charge_amount),
            "rendering_provider": billing.rendering_provider,
            "referring_provider": billing.referring_provider,
            "facility": billing.facility,
            "notes": billing.notes
        }
    
    def _convert_from_cerbo_format(self, cerbo_billing: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CERBO API format to local billing model"""
        return {
            "transaction_type": TransactionTypeEnum.CHARGE,
            "service_date": datetime.fromisoformat(cerbo_billing['service_date']) 
                          if cerbo_billing.get('service_date') else None,
            "procedure_code": cerbo_billing.get('procedure_code'),
            "procedure_description": cerbo_billing.get('procedure_description'),
            "diagnosis_code": cerbo_billing.get('diagnosis_code'),
            "diagnosis_description": cerbo_billing.get('diagnosis_description'),
            "charge_amount": cerbo_billing.get('charge_amount', 0),
            "balance_amount": cerbo_billing.get('balance_amount', cerbo_billing.get('charge_amount', 0)),
            "paid_amount": cerbo_billing.get('paid_amount', 0),
            "rendering_provider": cerbo_billing.get('rendering_provider'),
            "referring_provider": cerbo_billing.get('referring_provider'),
            "facility": cerbo_billing.get('facility'),
            "notes": cerbo_billing.get('notes'),
            "status": cerbo_billing.get('status', 'draft')
        }