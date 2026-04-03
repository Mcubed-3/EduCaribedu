from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import stripe


def _base_url() -> str:
    return os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")


def init_stripe() -> None:
    api_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing STRIPE_SECRET_KEY")
    stripe.api_key = api_key


def get_stripe_public_config() -> Dict[str, bool]:
    return {
        "publishable_key_present": bool(os.getenv("STRIPE_PUBLISHABLE_KEY", "").strip()),
        "price_id_pro_present": bool(os.getenv("STRIPE_PRICE_ID_PRO", "").strip()),
        "webhook_secret_present": bool(os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()),
    }


def create_checkout_session(*, user: Dict[str, Any]) -> Any:
    init_stripe()

    price_id = os.getenv("STRIPE_PRICE_ID_PRO", "").strip()
    if not price_id:
        raise RuntimeError("Missing STRIPE_PRICE_ID_PRO")

    return stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{_base_url()}/pricing?checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{_base_url()}/pricing?checkout=cancelled",
        client_reference_id=str(user["id"]),
        customer_email=user["email"],
        metadata={
            "user_id": str(user["id"]),
            "email": user["email"],
            "product": "educarib-pro",
        },
        subscription_data={
            "metadata": {
                "user_id": str(user["id"]),
                "email": user["email"],
                "product": "educarib-pro",
            }
        },
        allow_promotion_codes=True,
    )


def create_portal_session(*, customer_id: str) -> Any:
    init_stripe()
    return stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{_base_url()}/pricing",
    )


def verify_webhook(payload: bytes, signature: Optional[str]) -> Any:
    init_stripe()
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise RuntimeError("Missing STRIPE_WEBHOOK_SECRET")
    return stripe.Webhook.construct_event(payload=payload, sig_header=signature, secret=webhook_secret)


def to_iso_from_unix(ts: Optional[int]) -> str:
    if not ts:
        return ""
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
