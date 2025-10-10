"""Webhook routes for external services (Stripe, etc.)."""

from api.stripe import webhook_service
from config import get_settings
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
import stripe

routes = APIRouter(
    tags   = ["webhooks"],
    prefix = "/webhooks",
)


async def get_raw_body(request: Request) -> bytes:
    """Get raw request body for Stripe signature verification."""
    return await request.body()


@routes.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    stripe_signature: str = Header(alias = "stripe-signature"),
    body: bytes = Depends(get_raw_body),
):
    """Handle Stripe webhook events (unauthenticated, signature-verified)."""
    settings = get_settings()

    try:
        event = stripe.Webhook.construct_event(
            body,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET,
            tolerance=settings.STRIPE_WEBHOOK_TOLERANCE,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload") from None
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature") from None

    event_type: str = event["type"]

    try:
        if event_type in ["invoice.payment_succeeded", "invoice.paid", "invoice_payment.paid"]:
            await webhook_service.handle_payment_succeeded(event)
        elif event_type in ["invoice.payment_failed", "invoice_payment.failed"]:
            await webhook_service.handle_payment_failed(event)
        elif event_type in ["invoice.updated"]:
            await webhook_service.handle_invoice_updated(event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {e!s}") from e

    return {"status": "success"}
