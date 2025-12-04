import logging
from ..services.sap_client import SAPClient

logger = logging.getLogger(__name__)

class SimulationService:
    def __init__(self, sap_client: SAPClient):
        self.sap_client = sap_client

    def get_consumption_split(self, product, total_consumption):
        """
        Helper to split consumption for Double Tariff products.
        Returns (consumption_r1, consumption_r2)
        """
        consumption_r1 = total_consumption
        consumption_r2 = ""
        
        if product:
            is_dt = product.get('etDt') == 'DT' or product.get('preisNT') is not None
            if is_dt:
                try:
                    total = float(total_consumption)
                    consumption_r1 = int(total * 0.7)
                    consumption_r2 = int(total * 0.3)
                    logger.info(f"⚖️ Split consumption: R1={consumption_r1}, R2={consumption_r2}")
                except ValueError:
                    logger.warning("Could not split consumption, using default")
                    
        return consumption_r1, consumption_r2

    async def simulate_price(self, product_id, consumption, product=None, consumption_r1=None, consumption_r2=None):
        token = await self.sap_client.get_token()
        
        if consumption_r1 is None or consumption_r2 is None:
             consumption_r1, consumption_r2 = self.get_consumption_split(product, consumption)

        sim_result = await self.sap_client.simulate_price(token, consumption_r1, product_id, consumption_r2)
        return sim_result, consumption_r1, consumption_r2
