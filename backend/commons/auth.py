import os
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from dotenv import load_dotenv

load_dotenv()

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id= os.getenv('APP_CLIENT_ID'),
    tenant_id=os.getenv('TENANT_ID'),
    scopes={f'api://{os.getenv("APP_CLIENT_ID")}/access': 'Access'},
    allow_guest_users=True,
)