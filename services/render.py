import sys
import requests
from typing import Dict, Optional
from config import (
    RENDER_API_KEY,
    RENDER_OWNER_ID,
    RENDER_API_BASE,
    SERVICE_NAME,
    SERVICE_TYPE,
    RUNTIME,
    LANGSMITH_API_URL,
    LANGSMITH_PROJECT,
    LANGSMITH_API_KEY,
    OPENAI_API_KEY,
    REPO_URL,
    BRANCH,
    validate_env_vars,
)

# Server configuration
SERVER_START_COMMAND = "uvicorn services.server:app --host 0.0.0.0 --port $PORT"


def get_headers() -> Dict[str, str]:
    """Get headers for Render API requests."""
    if not RENDER_API_KEY:
        raise ValueError("RENDER_API_KEY environment variable is required")
    return {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


def check_service_exists(service_name: str) -> Optional[Dict]:
    """Check if a service with the given name already exists."""
    response = requests.get(
        f"{RENDER_API_BASE}/services",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        services = response.json()
        for service in services:
            svc_data = service.get("service", service)
            if svc_data.get("name") == service_name:
                return svc_data
    return None


def create_web_service(
    owner_id: str,
    service_name: str,
    repo_url: str,
    branch: str,
    env_vars: Dict[str, str]
) -> Dict:
    """Create a web service on Render with Git auto-deploy."""
    
    # Check if service already exists
    existing = check_service_exists(service_name)
    if existing:
        service_id = existing.get("id")
        print(f"Service '{service_name}' already exists (ID: {service_id})")
        print("Updating environment variables...")
        set_environment_variables(service_id, env_vars)
        return existing
    
    # Prepare service configuration
    service_config = {
        "type": SERVICE_TYPE,
        "name": service_name,
        "ownerId": owner_id,
        "plan": "free",
        "runtime": RUNTIME,
        "repo": repo_url,
        "branch": branch,
        "autoDeploy": True,
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": SERVER_START_COMMAND,
        "rootDir": ".",
    }
    
    print(f"Creating web service '{service_name}'...")
    response = requests.post(
        f"{RENDER_API_BASE}/services",
        headers=get_headers(),
        json=service_config
    )
    
    if response.status_code not in [200, 201]:
        error_msg = f"Failed to create service: {response.status_code} - {response.text}"
        raise RuntimeError(error_msg)
    
    service = response.json().get("service", response.json())
    service_id = service.get("id")
    print(f"✓ Service created successfully (ID: {service_id})")
    
    # Set environment variables
    if env_vars:
        set_environment_variables(service_id, env_vars)
    
    return service


def set_environment_variables(service_id: str, env_vars: Dict[str, str]) -> None:
    """Set environment variables for a service."""
    print(f"Setting environment variables...")
    
    for key, value in env_vars.items():
        response = requests.post(
            f"{RENDER_API_BASE}/services/{service_id}/env-vars",
            headers=get_headers(),
            json={
                "key": key,
                "value": value
            }
        )
        
        if response.status_code not in [200, 201]:
            raise RuntimeError(
                f"Failed to set environment variable {key}: {response.status_code} - {response.text}"
            )
    
    print(f"✓ Set {len(env_vars)} environment variable(s)")


def get_service_url(service_id: str) -> str:
    """Get the public URL for a service."""
    response = requests.get(
        f"{RENDER_API_BASE}/services/{service_id}",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        service = response.json().get("service", response.json())
        # Try different possible URL fields
        url = (
            service.get("serviceDetails", {}).get("url") or
            service.get("url") or
            f"https://{service.get('name')}.onrender.com"
        )
        return url
    
    # Fallback URL format
    return f"https://{SERVICE_NAME}.onrender.com"


def main():
    # Validate all required environment variables
    validate_env_vars()
    try:
        # Prepare environment variables
        env_vars = {
            "LANGSMITH_TRACING": "true",
            "LANGSMITH_ENDPOINT": LANGSMITH_API_URL,
            "LANGSMITH_API_KEY": LANGSMITH_API_KEY,
            "OPENAI_API_KEY": OPENAI_API_KEY,
        }
        
        # Add LANGSMITH_PROJECT if set
        if LANGSMITH_PROJECT:
            env_vars["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT
        
        # Create/update the service
        service = create_web_service(
            owner_id=RENDER_OWNER_ID,
            service_name=SERVICE_NAME,
            repo_url=REPO_URL,
            branch=BRANCH,
            env_vars=env_vars
        )
        
        service_id = service.get("id")
        service_url = get_service_url(service_id)
        webhook_url = f"{service_url}/webhook"
        return webhook_url
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
