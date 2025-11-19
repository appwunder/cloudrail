from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Any
import stripe

from app.core import deps
from app.core.config import settings
from app.models.user import User
from app.models.tenant import Tenant

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/create-checkout-session")
async def create_checkout_session(
    plan_type: str,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Create a Stripe Checkout Session
    """
    # Define price IDs (In production, these should be in config or DB)
    # Using test mode price IDs - YOU MUST REPLACE THESE WITH YOUR STRIPE PRICE IDS
    PRICES = {
        "pro": "price_1234567890", # Replace with actual Price ID
        "business": "price_0987654321", # Replace with actual Price ID
    }
    
    if plan_type not in PRICES:
        raise HTTPException(status_code=400, detail="Invalid plan type")
        
    price_id = PRICES[plan_type]
    
    # Get or create Stripe Customer
    tenant = current_user.tenant
    if not tenant.stripe_customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            name=tenant.name,
            metadata={
                "tenant_id": str(tenant.id),
                "tenant_slug": tenant.slug
            }
        )
        tenant.stripe_customer_id = customer.id
        db.commit()
        
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=tenant.stripe_customer_id,
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/billing/cancel",
            metadata={
                "tenant_id": str(tenant.id),
                "plan_type": plan_type
            }
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def webhook_received(request: Request, db: Session = Depends(deps.get_db)):
    """
    Handle Stripe Webhooks
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Fulfill the purchase...
        handle_checkout_session_completed(session, db)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription, db)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription, db)

    return {"status": "success"}

def handle_checkout_session_completed(session, db: Session):
    # Retrieve tenant_id from metadata
    tenant_id = session.get("metadata", {}).get("tenant_id")
    plan_type = session.get("metadata", {}).get("plan_type")
    
    if tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant:
            tenant.subscription_status = "active"
            tenant.subscription_plan = plan_type
            db.commit()

def handle_subscription_updated(subscription, db: Session):
    customer_id = subscription.get("customer")
    status = subscription.get("status")
    
    tenant = db.query(Tenant).filter(Tenant.stripe_customer_id == customer_id).first()
    if tenant:
        tenant.subscription_status = status
        db.commit()

def handle_subscription_deleted(subscription, db: Session):
    customer_id = subscription.get("customer")
    
    tenant = db.query(Tenant).filter(Tenant.stripe_customer_id == customer_id).first()
    if tenant:
        tenant.subscription_status = "canceled"
        tenant.subscription_plan = "free"
        db.commit()
