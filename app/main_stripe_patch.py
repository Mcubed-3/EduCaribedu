# Add these imports near the top of your main FastAPI file

from datetime import datetime, timezone

from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from stripe_service import (
    create_checkout_session,
    create_portal_session,
    get_stripe_public_config,
    to_iso_from_unix,
    verify_webhook,
)
from auth_service import (
    update_user_stripe_subscription,
    cancel_user_paid_plan,
    find_user_by_stripe_customer_id,
    find_user_by_stripe_subscription_id,
)

# Add these routes to your FastAPI app.
# Adjust get_current_user() if your project names it differently.

@app.get("/api/stripe/config")
def stripe_config():
    return get_stripe_public_config()


@app.post("/api/stripe/create-checkout-session")
def stripe_create_checkout_session(current_user=Depends(get_current_user)):
    if current_user["plan"] in {"pro", "admin"}:
        raise HTTPException(status_code=400, detail="You already have access to Pro.")

    try:
        session = create_checkout_session(user=current_user)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Stripe checkout setup failed: {exc}")

    return {"url": session.url, "id": session.id}


@app.post("/api/stripe/create-portal-session")
def stripe_create_portal_session(current_user=Depends(get_current_user)):
    if current_user["plan"] not in {"pro", "admin"}:
        raise HTTPException(status_code=400, detail="Billing portal is only available for paid plans.")

    customer_id = current_user.get("stripe_customer_id", "").strip()
    if not customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer is stored for this account yet.")

    try:
        session = create_portal_session(customer_id=customer_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Stripe billing portal failed: {exc}")

    return {"url": session.url}


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = verify_webhook(payload=payload, signature=sig)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid Stripe webhook: {exc}")

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id_raw = (obj.get("metadata") or {}).get("user_id") or obj.get("client_reference_id")
        if user_id_raw:
            user_id = int(user_id_raw)
            subscription_id = obj.get("subscription", "") or ""
            customer_id = obj.get("customer", "") or ""
            update_user_stripe_subscription(
                user_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                subscription_status="active",
                subscription_started_at=datetime.now(timezone.utc).isoformat(),
                billing_notes="Stripe Checkout completed",
            )

    elif event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        customer_id = obj.get("customer", "") or ""
        subscription_id = obj.get("id", "") or ""
        status = obj.get("status", "inactive")
        current_period_end = obj.get("current_period_end")
        metadata = obj.get("metadata") or {}
        user_id_raw = metadata.get("user_id")

        user_id = None
        if user_id_raw:
            user_id = int(user_id_raw)
        else:
            matched = find_user_by_stripe_customer_id(customer_id) or find_user_by_stripe_subscription_id(subscription_id)
            if matched:
                user_id = int(matched["id"])

        if user_id:
            update_user_stripe_subscription(
                user_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                subscription_status=status,
                subscription_started_at=datetime.now(timezone.utc).isoformat(),
                subscription_renews_at=to_iso_from_unix(current_period_end),
                billing_notes=f"Stripe subscription {status}",
            )

    elif event_type in {"customer.subscription.deleted", "invoice.payment_failed"}:
        customer_id = obj.get("customer", "") or ""
        subscription_id = obj.get("id", "") if event_type == "customer.subscription.deleted" else obj.get("subscription", "") or ""
        matched = find_user_by_stripe_subscription_id(subscription_id) or find_user_by_stripe_customer_id(customer_id)
        if matched:
            if event_type == "invoice.payment_failed":
                update_user_stripe_subscription(
                    int(matched["id"]),
                    stripe_customer_id=matched.get("stripe_customer_id", customer_id),
                    stripe_subscription_id=matched.get("stripe_subscription_id", subscription_id),
                    subscription_status="past_due",
                    subscription_started_at=matched.get("subscription_started_at", ""),
                    subscription_renews_at=matched.get("subscription_renews_at", ""),
                    billing_notes="Stripe invoice payment failed",
                )
            else:
                cancel_user_paid_plan(int(matched["id"]), note="Stripe subscription cancelled")

    return JSONResponse({"received": True})
