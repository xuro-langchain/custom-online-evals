import requests
from dataclasses import dataclass
from typing import Dict, Optional, Literal

from config import auth_headers, LANGSMITH_API_URL, client, LANGSMITH_PROJECT


@dataclass
class WebhookPayload:
    display_name: str
    webhook_url: str
    session_id: Optional[str] = None
    dataset_id: Optional[str] = None
    sampling_rate: float = 1.0
    is_enabled: bool = True
    filter: Optional[str] = None


def webhook_exists(name: str, webhook_url: str, target_type: Literal["dataset", "project"] = "dataset", target_id: str = None) -> bool:
    """Check if a webhook rule already exists with the same name, URL, and target."""
    url = f"{LANGSMITH_API_URL}/api/v1/runs/rules"

    params = {
        "dataset_id": target_id if target_type == "dataset" else None,
        "session_id": target_id if target_type == "project" else None,
        "name_contains": name
    }

    params = {k: v for k, v in params.items() if v is not None}
    existing = requests.get(url, headers=auth_headers(), params=params, timeout=30)
    if existing.status_code >= 300:
        raise RuntimeError(f"Failed to search for webhook '{name}': {existing.status_code} {existing.text}")
    
    existing_rules = existing.json()
    for rule in existing_rules:
        # Check if display name matches
        if rule.get("display_name") != name:
            continue
        
        # Check if target matches
        target_matches = False
        if target_type == "dataset" and rule.get("dataset_id") == target_id:
            target_matches = True
        elif target_type == "project" and rule.get("session_id") == target_id:
            target_matches = True
        
        if not target_matches:
            continue
        
        # Check if webhook URL matches (webhooks are stored as an array)
        webhooks = rule.get("webhooks", [])
        for webhook in webhooks:
            if isinstance(webhook, dict) and webhook.get("url") == webhook_url:
                return True
            elif isinstance(webhook, str) and webhook == webhook_url:
                return True
    return False


def _resolve_target_id(target_name: str, target_type: Literal["dataset", "project"] = "project") -> Optional[str]:
    """Resolve dataset or project name to ID."""
    if target_type == "dataset":
        datasets_iter = client.list_datasets(dataset_name=target_name)
        first_dataset = next(datasets_iter, None)
        if not first_dataset:
            print(f"    - Dataset '{target_name}' does not exist. Skipping webhook...")
            return None
        return str(first_dataset.id)
    elif target_type == "project":
        projects_iter = client.list_projects(name=target_name)
        first_project = next(projects_iter, None)
        if not first_project:
            print(f"    - Project '{target_name}' does not exist. Skipping webhook...")
            return None
        return str(first_project.id)


def create_webhook(name: str, webhook_url: str, target_name: str, target_type: Literal["dataset", "project"] = "project", 
                   sampling_rate: float = 1.0, filter: Optional[str] = None) -> Optional[Dict]:
    """Create a webhook rule."""
    target = _resolve_target_id(target_name, target_type)
    if not target:
        return None
    
    if webhook_exists(name, webhook_url, target_type, target):
        print(f"    - Webhook '{name}' with URL '{webhook_url}' already exists on the {target_type}. Skipping...")
        return None
    
    url = f"{LANGSMITH_API_URL}/runs/rules"
    
    body = {
        "display_name": name,
        "webhooks": [{
            "url": webhook_url,
        }],
        "session_id": target if target_type == "project" else None,
        "dataset_id": target if target_type == "dataset" else None,
        "sampling_rate": sampling_rate,
        "is_enabled": True,
        "filter": filter or "eq(is_root, true)",
    }
    # Remove None fields to satisfy API schema
    body = {k: v for k, v in body.items() if v is not None}

    resp = requests.post(url, headers=auth_headers(), json=body, timeout=30)
    if resp.status_code >= 300:
        raise RuntimeError(f"Failed to create webhook '{name}': {resp.status_code} {resp.text}")
    return resp.json()


def load_webhooks(webhook_url: str) -> None:
    """Create webhook rules for datasets and projects.
    
    Configure webhook URLs for each target. The webhook will be triggered
    when runs match the filter criteria.
    """
    print("Creating webhooks...")
    
    # Get webhook URL from environment variable
    if not webhook_url:
        raise ValueError("webhook_url is not set")
    
    # Project webhook
    create_webhook(
        name="feedback_aggregator",
        webhook_url=webhook_url,
        target_name=LANGSMITH_PROJECT,
        target_type="project",
    )

