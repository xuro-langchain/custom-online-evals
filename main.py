import sys
import time
import argparse
from config import validate_env_vars, setup_project, RENDER_URL
from services.render import main as deploy_service
from services.langsmith import load_webhooks
from services.traces import send_sample_traces


def main():
    """Main orchestration function."""
    parser = argparse.ArgumentParser(
        description="Set up LangSmith evaluation system with webhook judge service"
    )
    parser.add_argument(
        "--deploy-render",
        action="store_true",
        help="Attempt to deploy service to Render (default: skip deployment)"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("LangSmith Evaluation System Setup")
    print("=" * 60)
    print()
    
    # Step 1: Validate environment variables
    print("Step 1: Validating environment variables...")
    try:
        validate_env_vars(check_render=args.deploy_render)
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
    
    webhook_url = None
    
    # Step 3: Deploy service to Render (optional)
    if args.deploy_render:
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
        print()
    else:
        print("Step 3: Skipping Render deployment (use --deploy-render to enable)")
        print("  Note: You'll need to provide a webhook URL manually for webhook configuration")
        print()
    
    # Step 4: Configure webhooks in LangSmith
    if not webhook_url:
        webhook_url = RENDER_URL + '/webhook'
    try:    
        load_webhooks(webhook_url)
    except Exception as e:
        print(f"  ❌ Webhook configuration had issues: {e}")
        sys.exit(1)
    print("  ✓ Webhooks configured successfully")
    
    time.sleep(3)

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


if __name__ == "__main__":
    main()

