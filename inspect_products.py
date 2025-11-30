import asyncio
from backend.services.sap_client import sap_client

async def main():
    token = await sap_client.get_token()
    products = await sap_client.get_products(token)
    for p in products:
        if p.get('produktId') == 'INT_DNN24_DEMO_PROD':
            print(f"Product: {p}")
            print(f"etDt: {p.get('etDt')}")
            print(f"preisNT: {p.get('preisNT')}")

if __name__ == "__main__":
    asyncio.run(main())
