"""
Main orchestration script for setting up the evaluation system.

This script:
1. Sets up the LangSmith tracing project and sends initial trace
2. Deploys the webhook judge service to Render
3. Configures webhooks in LangSmith pointing to the deployed service
4. Sends sample traces to trigger the evaluators
"""

import sys
from config import validate_env_vars, setup_project, LANGSMITH_PROJECT
from services.render import main as deploy_service
from services.langsmith import load_webhooks
from services.traces import send_sample_traces


def main():
    """Main orchestration function."""
    print("=" * 60)
    print("LangSmith Evaluation System Setup")
    print("=" * 60)
    print()
    
    # Step 1: Validate environment variables
    print("Step 1: Validating environment variables...")
    try:
        validate_env_vars()
        print("  ✓ All required environment variables are set")
    except ValueError as e:
        print(f"  ❌ Validation failed: {e}")
        sys.exit(1)
    print()
    
    # Step 2: Set up tracing project and send initial trace
    print("Step 2: Setting up LangSmith tracing project...")
    try:
        setup_project()
        print("  ✓ Tracing project ready")
    except Exception as e:
        print(f"  ⚠ Warning: Project setup had issues: {e}")
        sys.exit(1)
    print()
    
    # Step 3: Deploy service to Render
    print("Step 3: Deploying service to Render...")
    try:
        url = deploy_service()
        if not url:
            raise RuntimeError("Deployment did not return a webhook URL")
        
        webhook_url = url + "/webhook"     
        print(f"  ✓ Service deployed successfully")
        print(f"  Webhook URL: {webhook_url}")
    except Exception as e:
        print(f"  ❌ Deployment failed: {e}")    
        sys.exit(1)
    
    # Step 4: Configure webhooks in LangSmith
    print("Step 4: Configuring webhooks in LangSmith...")
    try:
        load_webhooks(webhook_url)
        print("  ✓ Webhooks configured successfully")
    except Exception as e:
        print(f"  ❌ Webhook configuration had issues: {e}")
        sys.exit(1)
    
    # Step 5: Send sample traces to trigger evaluators
    print("Step 5: Sending sample traces...")
    try:
        send_sample_traces()
        print("  ✓ Sample traces sent")
    except Exception as e:
        print(f"  ❌ Failed to send sample traces: {e}")
        sys.exit(1)
    
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Check your Render dashboard to ensure the service is running")
    print("2. Check LangSmith dashboard to see traces and evaluations")
    print("3. Monitor webhook calls in your Render service logs")
    print()
    print(f"Webhook URL: {webhook_url}")


if __name__ == "__main__":
    main()

