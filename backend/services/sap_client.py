import requests
import base64
import logging
from typing import List, Dict, Any, Optional
from ..config import settings

logger = logging.getLogger(__name__)

class SAPClient:
    def __init__(self):
        self.token: Optional[str] = None
        
    def get_token(self) -> str:
        """
        Fetches an OAuth2 Bearer token from SAP.
        """
        if settings.MOCK_SAP:
            logger.warning("SAP credentials not found. Using Mock Token.")
            return "mock_token"

        # Basic Auth header with ClientID:ClientSecret
        credentials = f"{settings.SAP_CLIENT_ID}:{settings.SAP_CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
        
        data = {
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(settings.AUTH_URL, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            self.token = response.json().get("access_token")
            if not self.token:
                raise ValueError("No access token received")
            return self.token
        except Exception as e:
            logger.error(f"Error fetching token: {e}")
            return "mock_token"

    def get_products(self, token: str) -> List[Dict[str, Any]]:
        """
        Fetches products.
        Filter: vertriebskanal == 'Chatbot'
        """
        if token == "mock_token":
            return [
                {"name": "INTENSIVE 12 Demo-Produkt", "bezeichnung": "INTENSIVE 12 Demo-Produkt", "basePrice": 120.00, "workingPrice": 32.5, "vertriebskanal": "Chatbot"},
                {"name": "INTENSIVE 24 Demo-Produkt", "bezeichnung": "INTENSIVE 24 Demo-Produkt", "basePrice": 110.00, "workingPrice": 31.0, "vertriebskanal": "Chatbot"},
                {"name": "Green Energy Eco", "bezeichnung": "Green Energy Eco", "basePrice": 140.00, "workingPrice": 34.5, "vertriebskanal": "Chatbot", "oeko": True}
            ]

        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(settings.PRODUCT_URL, headers=headers, timeout=30)
            response.raise_for_status()
            all_products = response.json()
            
            logger.debug(f"📦 RAW SAP PRODUCT API RESPONSE: {all_products}")
            
            items = []
            if isinstance(all_products, list):
                items = all_products
            elif isinstance(all_products, dict):
                items = all_products.get('d', {}).get('results', []) or all_products.get('products', [])
            
            # Filter logic (Case insensitive)
            filtered_products = [
                p for p in items 
                if str(p.get('vertriebskanal', '')).lower() == 'chatbot'
            ]
            
            logger.info(f"📦 FILTERED PRODUCTS COUNT: {len(filtered_products)}")
            
            return filtered_products if filtered_products else items
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []

    def simulate_price(self, token: str, consumption_r1: float, product_id: str, consumption_r2: str = "") -> Optional[Dict[str, Any]]:
        """
        Simulates price.
        """
        if token == "mock_token":
            return {"total_price": 123.45, "currency": "EUR"}

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "ConsumptionR1": str(consumption_r1),
            "ProductID": str(product_id),
            "ConsumptionR2": str(consumption_r2)
        }
        
        logger.info(f"🚀 SIMULATION PAYLOAD: {payload}")
        
        try:
            response = requests.get(settings.SIMULATION_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            sim_result = response.json()
            logger.info(f"💰 RAW SIMULATION RESPONSE (GET): {sim_result}")
            return sim_result
        except Exception as e:
            logger.warning(f"GET Simulation failed: {e}. Trying POST...")
            try:
                response = requests.post(settings.SIMULATION_URL, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                sim_result = response.json()
                logger.info(f"💰 RAW SIMULATION RESPONSE (POST): {sim_result}")
                return sim_result
            except Exception as e2:
                logger.error(f"Error simulating price (POST): {e2}")
                if hasattr(e2, 'response') and e2.response is not None:
                     logger.error(f"SAP Error Response Body: {e2.response.text}")
                return None

    def create_offer(self, token: str, product_id: str, start_date: str, consumption_r1: float, consumption_r2: str = "", user_details: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Creates an offer.
        """
        if token == "mock_token":
            return {"offer_id": "OFFER-998877"}

        group_name = settings.SAP_OFFER_GROUP 
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Gruppe": group_name,
            "Produkt": str(product_id)
        }
        
        payload = {
            "STARTDATE": f"{start_date}"
        }
        
        logger.info(f"🚀 CREATE OFFER PAYLOAD: {payload}")
        
        try:
            response = requests.post(settings.OFFER_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating offer: {e}")
            if hasattr(e, 'response') and e.response is not None:
                 logger.error(f"SAP Error Response Body: {e.response.text}")
            return None

# Singleton instance
sap_client = SAPClient()
