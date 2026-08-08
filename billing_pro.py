"""
Billing module — Manual UPI Version (no payment gateway needed)
--------------------------------------------------------------------
- No Razorpay/Stripe account or KYC required.
- User pays directly to the admin's UPI ID (via a UPI deep link that
  opens their UPI app), then submits the transaction reference (UTR).
- The request sits as "pending" until the admin manually verifies the
  payment in their own UPI app and approves it from the admin panel.
- Same tier-tracking and daily-usage-limit functions as before, so
  image_studio_pro.py's Nano Banana gating keeps working unchanged.
"""

import datetime
import logging

import streamlit as st

logger = logging.getLogger(__name__)

FREE_NANO_BANANA_DAILY_LIMIT = 15


# ---------------------------------------------------------------------------
# Tier tracking (unchanged behaviour, just no payment-gateway dependency)
# ---------------------------------------------------------------------------

def get_user_tier(supabase, user_id: str) -> dict:
    cache_key = f"tier_{user_id}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    result = {"tier": "free", "pro_since": None}
    try:
        res = supabase.table("user_subscriptions").select("*").eq("user_id", user_id).limit(1).execute()
        if res.data:
            row = res.data[0]
            result = {"tier": row.get("tier", "free"), "pro_since": row.get("pro_since")}
    except Exception as e:
        logger.info("Could not load subscription (table may not exist yet): %s", e)

    st.session_state[cache_key] = result
    return result


def is_pro_user(supabase, user) -> bool:
    if not user:
        return False
    return get_user_tier(supabase, user.id)["tier"] == "pro"


def _activate_pro(supabase, user_id: str, note: str) -> bool:
    try:
        supabase.table("user_subscriptions").upsert({
            "user_id": user_id,
            "tier": "pro",
            "pro_since": datetime.datetime.utcnow().isoformat(),
            "last_payment_id": note,
        }).execute()
        st.session_state[f"tier_{user_id}"] = {"tier": "pro", "pro_since": datetime.datetime.utcnow().isoformat()}
        return True
    except Exception as e:
        st.error(
            f"🚨 Account Pro mark nahi ho paya: {e}\n\n"
            "Supabase mein `user_subscriptions` table honi chahiye: columns `user_id` text primary key, "
            "`tier` text, `pro_since` timestamptz, `last_payment_id` text"
        )
        return False


# ---------------------------------------------------------------------------
# Daily usage limiter (unchanged)
# ---------------------------------------------------------------------------

def check_and_consume_usage(supabase, user_id: str, feature: str, daily_limit: int) -> tuple:
    today = datetime.date.today().isoformat()
    row_id = f"{user_id}:{feature}:{today}"

    try:
        res = supabase.table("usage_counters").select("*").eq("id", row_id).limit(1).execute()
        used_today = res.data[0]["count"] if res.data else 0

        if used_today >= daily_limit:
            return False, used_today

        supabase.table("usage_counters").upsert({
            "id": row_id, "user_id": user_id, "feature": feature, "day": today, "count": used_today + 1,
        }).execute()
        return True, used_today + 1
    except Exception as e:
        logger.info("Usage counter table missing/unreachable, allowing by default: %s", e)
        return True, 0


# ---------------------------------------------------------------------------
# Manual payment requests
# ---------------------------------------------------------------------------

def submit_payment_request(supabase, user, amount_inr: float, utr: str, note: str = "") -> bool:
    try:
        supabase.table("payment_requests").insert({
            "user_id": user.id,
            "user_email": user.email,
            "amount": amount_inr,
            "utr": utr.strip(),
            "note": note.strip(),
            "status": "pending",
            "created_at": datetime.datetime.utcnow().isoformat(),
        }).execute()
        return True
    except Exception as e:
        st.error(
            f"🚨 Request submit nahi ho paya: {e}\n\n"
            "Supabase mein `payment_requests` table honi chahiye (SQL neeche di gayi hai)."
        )
        return False


def list_pending_requests(supabase) -> list:
    try:
        res = supabase.table("payment_requests").select("*").eq("status", "pending").order("created_at").execute()
        return res.data or []
    except Exception as e:
        logger.info("Could not load payment_requests: %s", e)
        return []


def approve_payment_request(supabase, request_id, user_id: str, utr: str) -> bool:
    if not _activate_pro(supabase, user_id, note=f"manual_utr_{utr}"):
        return False
    try:
        supabase.table("payment_requests").update({"status": "approved"}).eq("id", request_id).execute()
        return True
    except Exception as e:
        st.warning(f"User Pro ho gaya, lekin request status update nahi ho paya: {e}")
        return True


def reject_payment_request(supabase, request_id) -> bool:
    try:
        supabase.table("payment_requests").update({"status": "rejected"}).eq("id", request_id).execute()
        return True
    except Exception as e:
        st.error(f"Reject nahi ho paya: {e}")
        return False


# ---------------------------------------------------------------------------
# UI: user-facing upgrade flow
# ---------------------------------------------------------------------------

def render_manual_upgrade_ui(supabase, user, upi_id: str, amount_inr: float) -> None:
    if not upi_id:
        st.warning("⚠️ Payment abhi setup nahi hai. Admin ko UPI ID set karni hogi (Admin Assistant se 'upi_id' bolo).")
        return

    st.write(f"**Amount:** ₹{amount_inr:.0f}")
    st.write(f"**UPI ID:** `{upi_id}`")

    upi_link = f"upi://pay?pa={upi_id}&pn=AI%20Studio%20Hub&am={amount_inr:.0f}&cu=INR&tn=Pro%20Upgrade"
    st.link_button("📱 UPI App Se Pay Karo", upi_link, use_container_width=True)
    st.caption("Button dabane se tumhara UPI app (GPay/PhonePe/Paytm) khul jayega amount already bhara hua. Agar button kaam na kare to upar wali UPI ID pe manually bhi bhej sakte ho.")

    st.markdown("---")
    st.write("**Payment karne ke baad, transaction confirm karne ke liye:**")
    utr = st.text_input("UPI Transaction ID / UTR Number (payment app mein milega):")
    note = st.text_area("Koi extra note (optional):", height=70)

    if st.button("✅ Payment Submit Karo (Verification ke liye)", type="primary", use_container_width=True):
        if not utr.strip():
            st.warning("⚠️ Transaction ID/UTR daalna zaroori hai.")
        else:
            if submit_payment_request(supabase, user, amount_inr, utr, note):
                st.success("🎉 Submit ho gaya! Admin verify karke Pro activate kar dega — usually kuch ghanton mein ho jaata hai.")


# ---------------------------------------------------------------------------
# UI: admin approval panel
# ---------------------------------------------------------------------------

def render_admin_approval_panel(supabase) -> None:
    st.subheader("🧾 Pending Payment Approvals")
    pending = list_pending_requests(supabase)

    if not pending:
        st.info("Koi pending request nahi hai.")
        return

    for req in pending:
        with st.container(border=True):
            st.write(f"**User:** {req.get('user_email', '—')}")
            st.write(f"**Amount:** ₹{req.get('amount', '—')}")
            st.write(f"**UTR/Transaction ID:** `{req.get('utr', '—')}`")
            if req.get("note"):
                st.write(f"**Note:** {req['note']}")
            st.caption(f"Submitted: {req.get('created_at', '—')}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve (Pro activate karo)", key=f"approve_{req['id']}", use_container_width=True):
                    if approve_payment_request(supabase, req["id"], req["user_id"], req.get("utr", "")):
                        st.success(f"✅ {req.get('user_email')} ab Pro hai!")
                        st.rerun()
            with col2:
                if st.button("❌ Reject", key=f"reject_{req['id']}", use_container_width=True):
                    if reject_payment_request(supabase, req["id"]):
                        st.info("Reject kar diya.")
                        st.rerun()
