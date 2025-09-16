from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc, asc
from datetime import datetime, date, timedelta
import logging

from .base_repository import BaseRepository
from ..models.insurance import Insurance, InsuranceTypeEnum, CoverageStatusEnum, EligibilityStatusEnum
from ..models.patient import Patient
from ..api.cerbo_client import CerboClient, CerboAPIException

logger = logging.getLogger(__name__)

class InsuranceService(BaseRepository[Insurance]):
    """
    Insurance service with eligibility verification, coverage calculation, and CERBO API integration
    """
    
    def __init__(self, db: Session, cerbo_client: CerboClient = None):
        super().__init__(Insurance, db)
        self.cerbo_client = cerbo_client
    
    def search_insurance(
        self, 
        search_term: str, 
        search_type: str = "all",
        skip: int = 0, 
        limit: int = 100
    ) -> List[Insurance]:
        """
        Advanced insurance search with multiple criteria
        """
        try:
            if not search_term:
                return self.get_all(skip=skip, limit=limit)
            
            query = self.db.query(Insurance).join(Patient)
            
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
            elif search_type == "company":
                # Search by insurance company
                query = query.filter(Insurance.insurance_company.ilike(f"%{search_term}%"))
            elif search_type == "plan":
                # Search by plan name
                query = query.filter(Insurance.insurance_plan_name.ilike(f"%{search_term}%"))
            elif search_type == "policy":
                # Search by policy number
                query = query.filter(Insurance.policy_number.ilike(f"%{search_term}%"))
            elif search_type == "member_id":
                # Search by member ID
                query = query.filter(Insurance.member_id.ilike(f"%{search_term}%"))
            elif search_type == "group":
                # Search by group number
                query = query.filter(Insurance.group_number.ilike(f"%{search_term}%"))
            elif search_type == "subscriber":
                # Search by subscriber name
                query = query.filter(Insurance.subscriber_name.ilike(f"%{search_term}%"))
            elif search_type == "type":
                # Search by insurance type
                try:
                    insurance_type = InsuranceTypeEnum(search_term.lower())
                    query = query.filter(Insurance.insurance_type == insurance_type)
                except ValueError:
                    logger.warning(f"Invalid insurance type for search: {search_term}")
                    return []
            elif search_type == "status":
                # Search by coverage status
                try:
                    status = CoverageStatusEnum(search_term.lower())
                    query = query.filter(Insurance.coverage_status == status)
                except ValueError:
                    logger.warning(f"Invalid coverage status for search: {search_term}")
                    return []
            else:
                # Search all fields
                query = query.filter(
                    or_(
                        Insurance.insurance_company.ilike(f"%{search_term}%"),
                        Insurance.insurance_plan_name.ilike(f"%{search_term}%"),
                        Insurance.policy_number.ilike(f"%{search_term}%"),
                        Insurance.member_id.ilike(f"%{search_term}%"),
                        Insurance.group_number.ilike(f"%{search_term}%"),
                        Insurance.subscriber_name.ilike(f"%{search_term}%"),
                        Patient.first_name.ilike(f"%{search_term}%"),
                        Patient.last_name.ilike(f"%{search_term}%")
                    )
                )
            
            return query.filter(Insurance.is_active == True).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error searching insurance records: {e}")
            raise
    
    def get_patient_insurance(self, patient_id: int, active_only: bool = True) -> List[Insurance]:
        """Get all insurance records for a patient"""
        try:
            query = self.db.query(Insurance).filter(Insurance.patient_id == patient_id)
            
            if active_only:
                query = query.filter(Insurance.is_active == True)
            
            return query.order_by(Insurance.insurance_type.asc()).all()
            
        except Exception as e:
            logger.error(f"Error getting insurance for patient {patient_id}: {e}")
            raise
    
    def get_primary_insurance(self, patient_id: int) -> Optional[Insurance]:
        """Get primary insurance for a patient"""
        try:
            return self.db.query(Insurance).filter(
                and_(
                    Insurance.patient_id == patient_id,
                    Insurance.insurance_type == InsuranceTypeEnum.PRIMARY,
                    Insurance.is_active == True,
                    Insurance.coverage_status == CoverageStatusEnum.ACTIVE
                )
            ).first()
            
        except Exception as e:
            logger.error(f"Error getting primary insurance for patient {patient_id}: {e}")
            raise
    
    def get_secondary_insurance(self, patient_id: int) -> Optional[Insurance]:
        """Get secondary insurance for a patient"""
        try:
            return self.db.query(Insurance).filter(
                and_(
                    Insurance.patient_id == patient_id,
                    Insurance.insurance_type == InsuranceTypeEnum.SECONDARY,
                    Insurance.is_active == True,
                    Insurance.coverage_status == CoverageStatusEnum.ACTIVE
                )
            ).first()
            
        except Exception as e:
            logger.error(f"Error getting secondary insurance for patient {patient_id}: {e}")
            raise
    
    def get_by_policy_number(self, policy_number: str) -> Optional[Insurance]:
        """Get insurance by policy number"""
        return self.get_by_field("policy_number", policy_number)
    
    def get_by_member_id(self, member_id: str) -> Optional[Insurance]:
        """Get insurance by member ID"""
        return self.get_by_field("member_id", member_id)
    
    def get_by_cerbo_id(self, cerbo_id: str) -> Optional[Insurance]:
        """Get insurance by CERBO external ID"""
        return self.get_by_field("cerbo_insurance_id", cerbo_id)
    
    def get_expiring_insurance(self, days_ahead: int = 30) -> List[Insurance]:
        """Get insurance records expiring within specified days"""
        try:
            cutoff_date = date.today() + timedelta(days=days_ahead)
            
            return self.db.query(Insurance).filter(
                and_(
                    Insurance.termination_date <= cutoff_date,
                    Insurance.termination_date >= date.today(),
                    Insurance.is_active == True
                )
            ).order_by(Insurance.termination_date.asc()).all()
            
        except Exception as e:
            logger.error(f"Error getting expiring insurance: {e}")
            raise
    
    def get_insurance_needing_verification(self) -> List[Insurance]:
        """Get insurance records that need eligibility verification"""
        try:
            return self.db.query(Insurance).filter(
                and_(
                    Insurance.is_active == True,
                    Insurance.coverage_status == CoverageStatusEnum.ACTIVE,
                    or_(
                        Insurance.eligibility_status == EligibilityStatusEnum.UNKNOWN,
                        Insurance.eligibility_status == EligibilityStatusEnum.EXPIRED,
                        Insurance.next_verification_date <= datetime.utcnow()
                    )
                )
            ).order_by(Insurance.last_verification_date.asc()).all()
            
        except Exception as e:
            logger.error(f"Error getting insurance needing verification: {e}")
            raise
    
    async def verify_eligibility(self, insurance_id: int, force_verify: bool = False) -> Dict[str, Any]:
        """Verify insurance eligibility"""
        try:
            insurance = self.get_by_id(insurance_id)
            if not insurance:
                return {"success": False, "error": "Insurance record not found"}
            
            # Check if verification is needed
            if not force_verify and not insurance.needs_verification:
                return {
                    "success": True,
                    "message": "Verification not needed",
                    "status": insurance.eligibility_status.value,
                    "last_verified": insurance.last_verification_date.isoformat() if insurance.last_verification_date else None
                }
            
            verification_result = {"success": False, "status": EligibilityStatusEnum.FAILED}
            
            # Try CERBO API verification first
            if self.cerbo_client:
                try:
                    insurance_data = self._convert_to_cerbo_format(insurance)
                    cerbo_response = await self.cerbo_client.verify_insurance_eligibility(
                        insurance.patient.cerbo_patient_id, insurance_data
                    )
                    
                    if cerbo_response and cerbo_response.get('eligible'):
                        verification_result = {
                            "success": True,
                            "status": EligibilityStatusEnum.VERIFIED,
                            "response": cerbo_response,
                            "coverage_details": cerbo_response.get('coverage', {}),
                            "benefits": cerbo_response.get('benefits', {})
                        }
                    else:
                        verification_result = {
                            "success": False,
                            "status": EligibilityStatusEnum.FAILED,
                            "response": cerbo_response,
                            "error": cerbo_response.get('error', 'Eligibility verification failed')
                        }
                        
                except CerboAPIException as e:
                    logger.warning(f"CERBO eligibility verification failed for insurance {insurance_id}: {e}")
                    verification_result = {
                        "success": False,
                        "status": EligibilityStatusEnum.FAILED,
                        "error": f"API verification failed: {str(e)}"
                    }
            
            # Update insurance record with verification results
            update_data = {
                "eligibility_status": verification_result["status"],
                "last_verification_date": datetime.utcnow(),
                "next_verification_date": datetime.utcnow() + timedelta(days=30),  # Re-verify in 30 days
                "eligibility_response": str(verification_result.get("response", ""))
            }
            
            # Update coverage details if verification was successful
            if verification_result["success"] and verification_result.get("coverage_details"):
                coverage = verification_result["coverage_details"]
                if coverage.get("deductible_individual"):
                    update_data["deductible_individual"] = coverage["deductible_individual"]
                if coverage.get("deductible_family"):
                    update_data["deductible_family"] = coverage["deductible_family"]
                if coverage.get("out_of_pocket_max_individual"):
                    update_data["out_of_pocket_max_individual"] = coverage["out_of_pocket_max_individual"]
                if coverage.get("out_of_pocket_max_family"):
                    update_data["out_of_pocket_max_family"] = coverage["out_of_pocket_max_family"]
            
            self.update(insurance_id, update_data)
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Error verifying eligibility for insurance {insurance_id}: {e}")
            raise
    
    def calculate_patient_cost(
        self, 
        insurance_id: int, 
        service_cost: float, 
        service_type: str = "general",
        procedure_code: str = None
    ) -> Dict[str, Any]:
        """Calculate estimated patient cost for a service"""
        try:
            insurance = self.get_by_id(insurance_id)
            if not insurance:
                return {"error": "Insurance record not found"}
            
            if not insurance.is_active_coverage:
                return {
                    "patient_cost": service_cost,
                    "insurance_covers": 0,
                    "reason": "No active coverage",
                    "coverage_status": insurance.coverage_status.value
                }
            
            # Use the insurance model's built-in calculation method
            cost_breakdown = insurance.get_estimated_patient_cost(service_cost, service_type)
            
            # Add additional context
            cost_breakdown.update({
                "service_cost": service_cost,
                "service_type": service_type,
                "procedure_code": procedure_code,
                "insurance_company": insurance.insurance_company,
                "plan_name": insurance.insurance_plan_name,
                "deductible_remaining": insurance.deductible_remaining_individual,
                "verification_status": insurance.eligibility_status.value,
                "last_verified": insurance.last_verification_date.isoformat() if insurance.last_verification_date else None
            })
            
            return cost_breakdown
            
        except Exception as e:
            logger.error(f"Error calculating patient cost for insurance {insurance_id}: {e}")
            raise
    
    def process_deductible_payment(self, insurance_id: int, amount: float, description: str = None) -> Optional[Insurance]:
        """Process a payment toward deductible"""
        try:
            insurance = self.get_by_id(insurance_id)
            if not insurance:
                return None
            
            # Add to deductible met amount
            current_met = float(insurance.deductible_met_individual or 0)
            new_met = current_met + amount
            
            # Don't exceed the deductible amount
            if insurance.deductible_individual:
                max_deductible = float(insurance.deductible_individual)
                new_met = min(new_met, max_deductible)
            
            update_data = {"deductible_met_individual": new_met}
            
            # Add note if description provided
            if description:
                current_notes = insurance.notes or ""
                note = f"Deductible payment: ${amount:.2f} - {description}"
                update_data["notes"] = f"{current_notes}\n{note}".strip()
            
            return self.update(insurance_id, update_data)
            
        except Exception as e:
            logger.error(f"Error processing deductible payment for insurance {insurance_id}: {e}")
            raise
    
    def process_out_of_pocket_payment(self, insurance_id: int, amount: float, description: str = None) -> Optional[Insurance]:
        """Process a payment toward out-of-pocket maximum"""
        try:
            insurance = self.get_by_id(insurance_id)
            if not insurance:
                return None
            
            # Add to out-of-pocket met amount
            current_met = float(insurance.out_of_pocket_met_individual or 0)
            new_met = current_met + amount
            
            # Don't exceed the out-of-pocket maximum
            if insurance.out_of_pocket_max_individual:
                max_oop = float(insurance.out_of_pocket_max_individual)
                new_met = min(new_met, max_oop)
            
            update_data = {"out_of_pocket_met_individual": new_met}
            
            # Add note if description provided
            if description:
                current_notes = insurance.notes or ""
                note = f"Out-of-pocket payment: ${amount:.2f} - {description}"
                update_data["notes"] = f"{current_notes}\n{note}".strip()
            
            return self.update(insurance_id, update_data)
            
        except Exception as e:
            logger.error(f"Error processing out-of-pocket payment for insurance {insurance_id}: {e}")
            raise
    
    def get_benefits_summary(self, insurance_id: int) -> Dict[str, Any]:
        """Get comprehensive benefits summary for an insurance plan"""
        try:
            insurance = self.get_by_id(insurance_id)
            if not insurance:
                return None
            
            # Calculate remaining benefits
            deductible_progress = 0
            if insurance.deductible_individual and insurance.deductible_individual > 0:
                deductible_progress = (float(insurance.deductible_met_individual or 0) / float(insurance.deductible_individual)) * 100
            
            oop_progress = 0
            if insurance.out_of_pocket_max_individual and insurance.out_of_pocket_max_individual > 0:
                oop_progress = (float(insurance.out_of_pocket_met_individual or 0) / float(insurance.out_of_pocket_max_individual)) * 100
            
            return {
                "insurance": insurance.to_dict(),
                "benefits": {
                    "deductible": {
                        "individual_amount": float(insurance.deductible_individual) if insurance.deductible_individual else 0,
                        "family_amount": float(insurance.deductible_family) if insurance.deductible_family else 0,
                        "individual_met": float(insurance.deductible_met_individual) if insurance.deductible_met_individual else 0,
                        "family_met": float(insurance.deductible_met_family) if insurance.deductible_met_family else 0,
                        "individual_remaining": insurance.deductible_remaining_individual,
                        "family_remaining": insurance.deductible_remaining_family,
                        "individual_progress_percentage": round(deductible_progress, 2)
                    },
                    "out_of_pocket": {
                        "individual_max": float(insurance.out_of_pocket_max_individual) if insurance.out_of_pocket_max_individual else 0,
                        "family_max": float(insurance.out_of_pocket_max_family) if insurance.out_of_pocket_max_family else 0,
                        "individual_met": float(insurance.out_of_pocket_met_individual) if insurance.out_of_pocket_met_individual else 0,
                        "family_met": float(insurance.out_of_pocket_met_family) if insurance.out_of_pocket_met_family else 0,
                        "individual_progress_percentage": round(oop_progress, 2)
                    },
                    "copays": {
                        "primary_care": float(insurance.copay_primary_care) if insurance.copay_primary_care else None,
                        "specialist": float(insurance.copay_specialist) if insurance.copay_specialist else None,
                        "urgent_care": float(insurance.copay_urgent_care) if insurance.copay_urgent_care else None,
                        "emergency_room": float(insurance.copay_emergency_room) if insurance.copay_emergency_room else None
                    },
                    "coinsurance": {
                        "percentage": float(insurance.coinsurance_percentage) if insurance.coinsurance_percentage else None
                    },
                    "authorization": {
                        "requires_referral": insurance.requires_referral,
                        "requires_prior_auth": insurance.requires_prior_auth,
                        "prior_auth_number": insurance.prior_auth_number,
                        "prior_auth_expiration": insurance.prior_auth_expiration.isoformat() if insurance.prior_auth_expiration else None
                    }
                },
                "verification": {
                    "status": insurance.eligibility_status.value,
                    "last_verified": insurance.last_verification_date.isoformat() if insurance.last_verification_date else None,
                    "next_verification": insurance.next_verification_date.isoformat() if insurance.next_verification_date else None,
                    "needs_verification": insurance.needs_verification
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting benefits summary for insurance {insurance_id}: {e}")
            raise
    
    async def create_insurance_with_cerbo_sync(self, insurance_data: Dict[str, Any]) -> Insurance:
        """Create insurance locally and sync with CERBO API"""
        try:
            # Create insurance locally first
            insurance = self.create(insurance_data)
            
            # Sync with CERBO if client is available
            if self.cerbo_client:
                try:
                    cerbo_insurance_data = self._convert_to_cerbo_format(insurance)
                    cerbo_response = await self.cerbo_client.create_patient_insurance(
                        insurance.patient.cerbo_patient_id, cerbo_insurance_data
                    )
                    
                    # Update local insurance with CERBO ID
                    if cerbo_response and 'id' in cerbo_response:
                        self.update(insurance.id, {"cerbo_insurance_id": cerbo_response['id']})
                        logger.info(f"Insurance {insurance.id} synced with CERBO ID: {cerbo_response['id']}")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync insurance {insurance.id} with CERBO: {e}")
                    # Continue without CERBO sync
            
            return insurance
        except Exception as e:
            logger.error(f"Error creating insurance with CERBO sync: {e}")
            raise
    
    async def update_insurance_with_cerbo_sync(self, insurance_id: int, insurance_data: Dict[str, Any]) -> Optional[Insurance]:
        """Update insurance locally and sync with CERBO API"""
        try:
            # Update insurance locally
            insurance = self.update(insurance_id, insurance_data)
            if not insurance:
                return None
            
            # Sync with CERBO if client is available and insurance has CERBO ID
            if self.cerbo_client and insurance.cerbo_insurance_id:
                try:
                    cerbo_insurance_data = self._convert_to_cerbo_format(insurance)
                    await self.cerbo_client.update_patient_insurance(
                        insurance.patient.cerbo_patient_id, insurance.cerbo_insurance_id, cerbo_insurance_data
                    )
                    logger.info(f"Insurance {insurance.id} updated in CERBO")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync insurance {insurance.id} update with CERBO: {e}")
                    # Continue without CERBO sync
            
            return insurance
        except Exception as e:
            logger.error(f"Error updating insurance with CERBO sync: {e}")
            raise
    
    async def sync_from_cerbo(self, cerbo_insurance_id: str, patient_id: int) -> Optional[Insurance]:
        """Sync insurance data from CERBO API"""
        if not self.cerbo_client:
            raise ValueError("CERBO client not available")
        
        try:
            # Get patient's CERBO ID
            patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient or not patient.cerbo_patient_id:
                raise ValueError(f"Patient {patient_id} not found or missing CERBO ID")
            
            # Get insurance data from CERBO
            cerbo_insurance = await self.cerbo_client.get_patient_insurance(patient.cerbo_patient_id)
            
            if not cerbo_insurance:
                return None
            
            # Find the specific insurance record in the response
            insurance_record = None
            if isinstance(cerbo_insurance, list):
                insurance_record = next((ins for ins in cerbo_insurance if ins.get('id') == cerbo_insurance_id), None)
            elif cerbo_insurance.get('id') == cerbo_insurance_id:
                insurance_record = cerbo_insurance
            
            if not insurance_record:
                return None
            
            # Check if insurance already exists locally
            existing_insurance = self.get_by_cerbo_id(cerbo_insurance_id)
            
            # Convert CERBO data to local format
            insurance_data = self._convert_from_cerbo_format(insurance_record)
            insurance_data['cerbo_insurance_id'] = cerbo_insurance_id
            insurance_data['patient_id'] = patient_id
            
            if existing_insurance:
                # Update existing insurance
                return self.update(existing_insurance.id, insurance_data)
            else:
                # Create new insurance
                return self.create(insurance_data)
                
        except CerboAPIException as e:
            logger.error(f"Error syncing insurance from CERBO: {e}")
            raise
    
    def get_insurance_statistics(self, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get insurance statistics"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Get all active insurance records
            all_insurance = self.db.query(Insurance).filter(Insurance.is_active == True).all()
            
            # Count by type
            type_counts = {}
            for ins_type in InsuranceTypeEnum:
                type_counts[ins_type.value] = len([ins for ins in all_insurance if ins.insurance_type == ins_type])
            
            # Count by status
            status_counts = {}
            for status in CoverageStatusEnum:
                status_counts[status.value] = len([ins for ins in all_insurance if ins.coverage_status == status])
            
            # Count by eligibility status
            eligibility_counts = {}
            for status in EligibilityStatusEnum:
                eligibility_counts[status.value] = len([ins for ins in all_insurance if ins.eligibility_status == status])
            
            # Get expiring insurance
            expiring_insurance = self.get_expiring_insurance(30)
            need_verification = self.get_insurance_needing_verification()
            
            # Top insurance companies
            company_counts = {}
            for insurance in all_insurance:
                company = insurance.insurance_company
                company_counts[company] = company_counts.get(company, 0) + 1
            
            top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "totals": {
                    "total_active_policies": len(all_insurance),
                    "expiring_soon": len(expiring_insurance),
                    "need_verification": len(need_verification),
                    "unique_patients": len(set(ins.patient_id for ins in all_insurance))
                },
                "by_type": type_counts,
                "by_coverage_status": status_counts,
                "by_eligibility_status": eligibility_counts,
                "top_insurance_companies": [{"company": company, "count": count} for company, count in top_companies],
                "alerts": {
                    "expiring_policies": [ins.to_dict() for ins in expiring_insurance[:10]],  # First 10
                    "verification_needed": [ins.to_dict() for ins in need_verification[:10]]   # First 10
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting insurance statistics: {e}")
            raise
    
    def _convert_to_cerbo_format(self, insurance: Insurance) -> Dict[str, Any]:
        """Convert local insurance model to CERBO API format"""
        return {
            "type": insurance.insurance_type.value if insurance.insurance_type else None,
            "company": insurance.insurance_company,
            "plan_name": insurance.insurance_plan_name,
            "plan_type": insurance.insurance_plan_type,
            "policy_number": insurance.policy_number,
            "group_number": insurance.group_number,
            "member_id": insurance.member_id,
            "subscriber": {
                "name": insurance.subscriber_name,
                "relationship": insurance.subscriber_relationship,
                "date_of_birth": insurance.subscriber_date_of_birth.isoformat() if insurance.subscriber_date_of_birth else None,
                "gender": insurance.subscriber_gender
            },
            "coverage": {
                "effective_date": insurance.effective_date.isoformat() if insurance.effective_date else None,
                "termination_date": insurance.termination_date.isoformat() if insurance.termination_date else None,
                "status": insurance.coverage_status.value if insurance.coverage_status else None
            },
            "benefits": {
                "deductible_individual": float(insurance.deductible_individual) if insurance.deductible_individual else None,
                "deductible_family": float(insurance.deductible_family) if insurance.deductible_family else None,
                "out_of_pocket_max_individual": float(insurance.out_of_pocket_max_individual) if insurance.out_of_pocket_max_individual else None,
                "out_of_pocket_max_family": float(insurance.out_of_pocket_max_family) if insurance.out_of_pocket_max_family else None,
                "copay_primary_care": float(insurance.copay_primary_care) if insurance.copay_primary_care else None,
                "copay_specialist": float(insurance.copay_specialist) if insurance.copay_specialist else None,
                "coinsurance_percentage": float(insurance.coinsurance_percentage) if insurance.coinsurance_percentage else None
            },
            "contact": {
                "customer_service_phone": insurance.customer_service_phone,
                "claims_address": insurance.claims_address
            }
        }
    
    def _convert_from_cerbo_format(self, cerbo_insurance: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CERBO API format to local insurance model"""
        subscriber = cerbo_insurance.get('subscriber', {})
        coverage = cerbo_insurance.get('coverage', {})
        benefits = cerbo_insurance.get('benefits', {})
        contact = cerbo_insurance.get('contact', {})
        
        return {
            "insurance_type": cerbo_insurance.get('type'),
            "insurance_company": cerbo_insurance.get('company'),
            "insurance_plan_name": cerbo_insurance.get('plan_name'),
            "insurance_plan_type": cerbo_insurance.get('plan_type'),
            "policy_number": cerbo_insurance.get('policy_number'),
            "group_number": cerbo_insurance.get('group_number'),
            "member_id": cerbo_insurance.get('member_id'),
            "subscriber_name": subscriber.get('name'),
            "subscriber_relationship": subscriber.get('relationship'),
            "subscriber_date_of_birth": datetime.strptime(subscriber['date_of_birth'], "%Y-%m-%d").date() 
                                      if subscriber.get('date_of_birth') else None,
            "subscriber_gender": subscriber.get('gender'),
            "effective_date": datetime.strptime(coverage['effective_date'], "%Y-%m-%d").date() 
                            if coverage.get('effective_date') else None,
            "termination_date": datetime.strptime(coverage['termination_date'], "%Y-%m-%d").date() 
                              if coverage.get('termination_date') else None,
            "coverage_status": coverage.get('status', 'active'),
            "deductible_individual": benefits.get('deductible_individual'),
            "deductible_family": benefits.get('deductible_family'),
            "out_of_pocket_max_individual": benefits.get('out_of_pocket_max_individual'),
            "out_of_pocket_max_family": benefits.get('out_of_pocket_max_family'),
            "copay_primary_care": benefits.get('copay_primary_care'),
            "copay_specialist": benefits.get('copay_specialist'),
            "coinsurance_percentage": benefits.get('coinsurance_percentage'),
            "customer_service_phone": contact.get('customer_service_phone'),
            "claims_address": contact.get('claims_address')
        }