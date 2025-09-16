import os
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from urllib.parse import urljoin
import base64

logger = logging.getLogger(__name__)

class CerboAPIException(Exception):
    """Custom exception for Cerbo API errors"""
    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)

class RateLimiter:
    """Simple rate limiter for API requests"""
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def wait_if_needed(self):
        now = datetime.utcnow()
        # Remove requests outside the time window
        self.requests = [req_time for req_time in self.requests 
                        if (now - req_time).total_seconds() < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            # Wait until we can make another request
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds.")
                await asyncio.sleep(wait_time)
        
        self.requests.append(now)

class CerboClient:
    """
    Async client for CERBO SANDBOX API integration
    
    Documentation: https://docs.cer.bo/
    """
    
    def __init__(
        self,
        base_url: str = None,
        username: str = None,
        secret_key: str = None,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_requests: int = 60,
        rate_limit_window: int = 60
    ):
        # Use environment variables or defaults
        self.base_url = base_url or os.getenv("CERBO_BASE_URL", "https://sandbox.md-hq.com/api/v1")
        self.username = username or os.getenv("CERBO_USERNAME", "pk_scribe_health_ai")
        self.secret_key = secret_key or os.getenv("CERBO_SECRET_KEY", "sk_FghBAQHKXZzO4Mt4oWAC5s8sGEbVH")
        
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limiter = RateLimiter(rate_limit_requests, rate_limit_window)
        
        # Create basic auth header
        credentials = f"{self.username}:{self.secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"
        
        self.session = None
        
        logger.info(f"Initialized Cerbo client for {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "EHR-Dashboard/1.0"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        retry_count: int = 0
    ) -> Dict:
        """
        Make an HTTP request to the Cerbo API with error handling and retries
        """
        await self.rate_limiter.wait_if_needed()
        
        url = urljoin(self.base_url.rstrip('/') + '/', endpoint.lstrip('/'))
        
        try:
            if not self.session:
                raise CerboAPIException("Client session not initialized. Use async context manager.")
            
            logger.debug(f"Making {method} request to {url}")
            
            async with self.session.request(
                method=method,
                url=url,
                json=data if data else None,
                params=params
            ) as response:
                
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        return json.loads(response_text) if response_text else {}
                    except json.JSONDecodeError:
                        return {"raw_response": response_text}
                
                elif response.status == 401:
                    raise CerboAPIException(
                        "Authentication failed. Check credentials.",
                        status_code=response.status
                    )
                
                elif response.status == 403:
                    raise CerboAPIException(
                        "Access forbidden. Check permissions.",
                        status_code=response.status
                    )
                
                elif response.status == 404:
                    raise CerboAPIException(
                        f"Resource not found: {endpoint}",
                        status_code=response.status
                    )
                
                elif response.status == 429:
                    # Rate limited - implement exponential backoff
                    if retry_count < self.max_retries:
                        wait_time = (2 ** retry_count) * 1
                        logger.warning(f"Rate limited. Retrying in {wait_time} seconds.")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(method, endpoint, data, params, retry_count + 1)
                    else:
                        raise CerboAPIException(
                            "Rate limit exceeded. Max retries reached.",
                            status_code=response.status
                        )
                
                elif response.status >= 500:
                    # Server error - retry with exponential backoff
                    if retry_count < self.max_retries:
                        wait_time = (2 ** retry_count) * 1
                        logger.warning(f"Server error {response.status}. Retrying in {wait_time} seconds.")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(method, endpoint, data, params, retry_count + 1)
                    else:
                        raise CerboAPIException(
                            f"Server error {response.status}. Max retries reached.",
                            status_code=response.status,
                            response_data={"response": response_text}
                        )
                
                else:
                    # Other client errors
                    try:
                        error_data = json.loads(response_text) if response_text else {}
                    except json.JSONDecodeError:
                        error_data = {"raw_response": response_text}
                    
                    raise CerboAPIException(
                        f"API request failed with status {response.status}",
                        status_code=response.status,
                        response_data=error_data
                    )
        
        except aiohttp.ClientError as e:
            if retry_count < self.max_retries:
                wait_time = (2 ** retry_count) * 1
                logger.warning(f"Network error: {e}. Retrying in {wait_time} seconds.")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            else:
                raise CerboAPIException(f"Network error: {e}")
    
    # Patient API methods
    async def get_patients(self, page: int = 1, limit: int = 50, search: str = None) -> Dict:
        """Get list of patients"""
        params = {"page": page, "limit": limit}
        if search:
            params["search"] = search
        
        return await self._make_request("GET", "/patients", params=params)
    
    async def get_patient(self, patient_id: str) -> Dict:
        """Get a specific patient by ID"""
        return await self._make_request("GET", f"/patients/{patient_id}")
    
    async def create_patient(self, patient_data: Dict) -> Dict:
        """Create a new patient"""
        return await self._make_request("POST", "/patients", data=patient_data)
    
    async def update_patient(self, patient_id: str, patient_data: Dict) -> Dict:
        """Update an existing patient"""
        return await self._make_request("PUT", f"/patients/{patient_id}", data=patient_data)
    
    async def search_patients(self, query: str, search_type: str = "name") -> Dict:
        """Search patients by various criteria"""
        params = {"q": query, "type": search_type}
        return await self._make_request("GET", "/patients/search", params=params)
    
    # Appointment API methods
    async def get_appointments(
        self, 
        start_date: str = None, 
        end_date: str = None,
        provider_id: str = None,
        patient_id: str = None,
        status: str = None
    ) -> Dict:
        """Get appointments with optional filters"""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if provider_id:
            params["provider_id"] = provider_id
        if patient_id:
            params["patient_id"] = patient_id
        if status:
            params["status"] = status
        
        return await self._make_request("GET", "/appointments", params=params)
    
    async def get_appointment(self, appointment_id: str) -> Dict:
        """Get a specific appointment by ID"""
        return await self._make_request("GET", f"/appointments/{appointment_id}")
    
    async def create_appointment(self, appointment_data: Dict) -> Dict:
        """Create a new appointment"""
        return await self._make_request("POST", "/appointments", data=appointment_data)
    
    async def update_appointment(self, appointment_id: str, appointment_data: Dict) -> Dict:
        """Update an existing appointment"""
        return await self._make_request("PUT", f"/appointments/{appointment_id}", data=appointment_data)
    
    async def cancel_appointment(self, appointment_id: str, reason: str = None) -> Dict:
        """Cancel an appointment"""
        data = {"status": "cancelled"}
        if reason:
            data["cancellation_reason"] = reason
        return await self._make_request("PUT", f"/appointments/{appointment_id}", data=data)
    
    # Provider API methods
    async def get_providers(self) -> Dict:
        """Get list of providers"""
        return await self._make_request("GET", "/providers")
    
    async def get_provider(self, provider_id: str) -> Dict:
        """Get a specific provider by ID"""
        return await self._make_request("GET", f"/providers/{provider_id}")
    
    async def get_provider_schedule(self, provider_id: str, date: str) -> Dict:
        """Get provider schedule for a specific date"""
        params = {"date": date}
        return await self._make_request("GET", f"/providers/{provider_id}/schedule", params=params)
    
    # Clinical Records API methods
    async def get_patient_records(self, patient_id: str, record_type: str = None) -> Dict:
        """Get clinical records for a patient"""
        params = {}
        if record_type:
            params["type"] = record_type
        return await self._make_request("GET", f"/patients/{patient_id}/records", params=params)
    
    async def create_clinical_record(self, patient_id: str, record_data: Dict) -> Dict:
        """Create a new clinical record"""
        return await self._make_request("POST", f"/patients/{patient_id}/records", data=record_data)
    
    async def get_clinical_record(self, record_id: str) -> Dict:
        """Get a specific clinical record"""
        return await self._make_request("GET", f"/records/{record_id}")
    
    async def update_clinical_record(self, record_id: str, record_data: Dict) -> Dict:
        """Update a clinical record"""
        return await self._make_request("PUT", f"/records/{record_id}", data=record_data)
    
    # Insurance and Eligibility methods
    async def verify_insurance_eligibility(self, patient_id: str, insurance_data: Dict) -> Dict:
        """Verify insurance eligibility for a patient"""
        return await self._make_request("POST", f"/patients/{patient_id}/insurance/verify", data=insurance_data)
    
    async def get_patient_insurance(self, patient_id: str) -> Dict:
        """Get insurance information for a patient"""
        return await self._make_request("GET", f"/patients/{patient_id}/insurance")
    
    # Billing methods
    async def get_patient_billing(self, patient_id: str) -> Dict:
        """Get billing information for a patient"""
        return await self._make_request("GET", f"/patients/{patient_id}/billing")
    
    async def create_charge(self, billing_data: Dict) -> Dict:
        """Create a billing charge"""
        return await self._make_request("POST", "/billing/charges", data=billing_data)
    
    async def process_payment(self, payment_data: Dict) -> Dict:
        """Process a payment"""
        return await self._make_request("POST", "/billing/payments", data=payment_data)
    
    # Utility methods
    async def test_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            response = await self._make_request("GET", "/health")
            return True
        except CerboAPIException as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_api_info(self) -> Dict:
        """Get API information and status"""
        return await self._make_request("GET", "/info")


# Convenience function for creating client
def create_cerbo_client(**kwargs) -> CerboClient:
    """Create a new Cerbo client instance"""
    return CerboClient(**kwargs)