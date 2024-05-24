from azure.identity import InteractiveBrowserCredential

def authenticate(tenant_id):
    credential = InteractiveBrowserCredential(tenant_id=tenant_id)
    return credential
