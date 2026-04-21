# -*- coding: utf-8 -*-
"""
NicheFlow AI — main.py FIXED v4
- /pipeline endpoint fixed: stores body_images_bytes in session cache for Pinterest
- /pinterest/run fixed: passes pin_image_prompt, wp_url, wp_password to run_pinterest_bot
- /webhook/lemonsqueezy fixed: hmac.new → hmac.new corrected
- All other endpoints unchanged
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import requests
import os
import time
import hmac
import hashlib
import json

from generator import (
    run_full_pipeline, generate_article, run_pinterest_bot,
    get_pinterest_boards, test_gemini_key, test_goapi_key,
    test_wordpress, test_pinterest, fetch_internal_links, fetch_wp_categories,
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gfulpvqqpakcgubkilwc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_U9zJp_BBd-jkJCwvGimNmw_E4NyynFN")
SUPABASE_SECRET = os.getenv("SUPABASE_SECRET", "sb_secret_u_ZtMx7jmUBxXgOxhxYmaw_izKuJCyC")
LEMONSQUEEZY_SECRET = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")

LEMON_BASIC_VARIANT_ID = os.getenv("LEMON_BASIC_VARIANT_ID", "")
LEMON_PRO_VARIANT_ID   = os.getenv("LEMON_PRO_VARIANT_ID", "")

app = FastAPI(title="NicheFlow AI API", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# In-memory cache: stores body image bytes per article URL for Pinterest pin image generation
# Key: post_url, Value: list of raw bytes (body images 1-3)
_article_image_cache: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
#  Supabase helpers
# ─────────────────────────────────────────────────────────────────────────────

def supa_headers(user_token=None):
    token = user_token or SUPABASE_KEY
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {token}",
            "Content-Type": "application/json", "Prefer": "return=representation"}


def supa_get_user(token):
    resp = requests.get(f"{SUPABASE_URL}/auth/v1/user",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {token}"}, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return resp.json()


def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = authorization.split(" ", 1)[1]
    return supa_get_user(token), token


def get_user_settings(user_id, token):
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/settings?user_id=eq.{user_id}&select=*",
        headers=supa_headers(token), timeout=10)
    if resp.status_code == 200:
        rows = resp.json()
        return rows[0] if rows else {}
    return {}


def get_user_plan(user_id, token):
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=plan",
        headers=supa_headers(token), timeout=10)
    if resp.status_code == 200:
        rows = resp.json()
        return rows[0].get("plan", "basic") if rows else "basic"
    return "basic"


def save_article_to_db(user_id, token, title, result, publish_status):
    data = {
        "user_id": user_id,
        "title": title,
        "post_url": result.get("post_url", ""),
        "post_id": str(result.get("post_id", "")),
        "featured_image_url": result.get("featured_image_url", ""),
        "status": "published" if result.get("success") else "failed",
        "wp_status": publish_status,
        "error": result.get("error", ""),
    }
    resp = requests.post(f"{SUPABASE_URL}/rest/v1/articles", headers=supa_headers(token), json=data, timeout=10)
    if resp.status_code in (200, 201):
        rows = resp.json()
        return rows[0]["id"] if rows else None
    return None


def upgrade_user_plan(user_email: str, plan: str):
    """Called by LemonSqueezy webhook to upgrade a user."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_SECRET}",
        "Content-Type": "application/json",
    }
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/profiles?email=eq.{user_email}&select=id",
        headers=headers, timeout=10
    )
    if resp.status_code == 200 and resp.json():
        user_id = resp.json()[0]["id"]
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}",
            headers={**headers, "Prefer": "return=representation"},
            json={"plan": plan},
            timeout=10,
        )
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
#  Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    gemini_key: Optional[str] = ""
    goapi_key: Optional[str] = ""
    wp_url: Optional[str] = ""
    wp_password: Optional[str] = ""
    publish_status: Optional[str] = "draft"
    custom_prompt: Optional[str] = ""
    card_prompt: Optional[str] = ""
    mj_template: Optional[str] = ""
    use_pollinations: Optional[bool] = False
    pollinations_prompt: Optional[str] = ""
    show_card: Optional[bool] = True
    use_internal_links: Optional[bool] = True
    max_links: Optional[int] = 4
    delay_sec: Optional[int] = 10
    pinterest_token: Optional[str] = ""
    auto_pin: Optional[bool] = False
    pin_delay_min: Optional[int] = 0
    pinterest_prompt: Optional[str] = ""
    pinterest_boards: Optional[str] = ""
    pin_image_prompt: Optional[str] = ""  # NEW: pin image design prompt


class PipelineRequest(BaseModel):
    title: str
    gemini_key: Optional[str] = ""
    goapi_key: Optional[str] = ""
    wp_url: Optional[str] = ""
    wp_password: Optional[str] = ""
    custom_prompt: Optional[str] = ""
    card_prompt: Optional[str] = ""
    mj_template: Optional[str] = ""
    publish_status: Optional[str] = "publish"
    use_images: Optional[bool] = False
    use_pollinations: Optional[bool] = False
    pollinations_prompt: Optional[str] = ""
    show_card: Optional[bool] = True
    category_ids: Optional[List[int]] = None
    use_internal_links: Optional[bool] = True
    max_links: Optional[int] = 4


class GenerateRequest(BaseModel):
    titles: List[str]
    draft: Optional[bool] = False
    use_images: Optional[bool] = False
    delay_sec: Optional[int] = 10
    category_ids: Optional[List[int]] = None


class PreviewRequest(BaseModel):
    title: str


class TestRequest(BaseModel):
    key_type: str
    value: str
    wp_password: Optional[str] = ""


class PinterestRunRequest(BaseModel):
    article_ids: Optional[List[str]] = None
    board_ids: List[str]
    pin_image_prompt: Optional[str] = ""  # NEW: passed from frontend


# ─────────────────────────────────────────────────────────────────────────────
#  HEALTH
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
@app.get("/health")
def health():
    return {"status": "ok", "service": "NicheFlow AI", "version": "4.0.0"}


# ─────────────────────────────────────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/auth/signup")
def signup(body: dict):
    resp = requests.post(f"{SUPABASE_URL}/auth/v1/signup",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": body["email"], "password": body["password"]}, timeout=15)
    data = resp.json()
    if resp.status_code in (200, 201):
        return {"success": True, "message": "Check your email to confirm your account."}
    raise HTTPException(status_code=400, detail=data.get("error_description", data.get("msg", "Signup failed")))


@app.post("/auth/login")
def login(body: dict):
    resp = requests.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": body["email"], "password": body["password"]}, timeout=15)
    data = resp.json()
    if resp.status_code == 200:
        return {"success": True, "access_token": data["access_token"], "user": data["user"]}
    raise HTTPException(status_code=401, detail=data.get("error_description", "Login failed"))


# ─────────────────────────────────────────────────────────────────────────────
#  SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/settings")
def get_settings(auth=Depends(get_current_user)):
    user, token = auth
    cfg = get_user_settings(user["id"], token)
    plan = get_user_plan(user["id"], token)
    return {"settings": cfg, "plan": plan}


@app.post("/settings")
def save_settings(body: SettingsUpdate, auth=Depends(get_current_user)):
    user, token = auth
    data = body.dict()
    data["user_id"] = user["id"]
    resp = requests.post(f"{SUPABASE_URL}/rest/v1/settings",
        headers={**supa_headers(token), "Prefer": "resolution=merge-duplicates,return=representation"},
        json=data, timeout=15)
    if resp.status_code in (200, 201):
        return {"success": True}
    raise HTTPException(status_code=500, detail=f"Save failed: {resp.text[:200]}")


# ─────────────────────────────────────────────────────────────────────────────
#  TEST
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/test")
def test_connection(body: TestRequest, auth=Depends(get_current_user)):
    if body.key_type == "ai": return test_gemini_key(body.value)
    elif body.key_type == "goapi": return test_goapi_key(body.value)
    elif body.key_type == "wp": return test_wordpress(body.value, body.wp_password or "")
    elif body.key_type == "pinterest": return test_pinterest(body.value)
    raise HTTPException(status_code=400, detail="Unknown key_type")


# ─────────────────────────────────────────────────────────────────────────────
#  WORDPRESS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/wp/categories")
def wp_categories(auth=Depends(get_current_user)):
    user, token = auth
    cfg = get_user_settings(user["id"], token)
    return {"categories": fetch_wp_categories(cfg.get("wp_url",""), cfg.get("wp_password",""))}


@app.get("/wp/posts")
def wp_posts(auth=Depends(get_current_user)):
    user, token = auth
    cfg = get_user_settings(user["id"], token)
    return {"posts": fetch_internal_links(cfg.get("wp_url",""), cfg.get("wp_password",""), max_posts=200)}


# ─────────────────────────────────────────────────────────────────────────────
#  /pipeline — React frontend calls this with all config in body
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/pipeline")
def pipeline_direct(body: PipelineRequest, authorization: str = Header(None)):
    if not body.gemini_key or not body.gemini_key.strip():
        raise HTTPException(status_code=400, detail="No AI key. Go to Settings → API Keys.")
    if not body.wp_url or not body.wp_url.strip():
        raise HTTPException(status_code=400, detail="No WordPress URL. Go to Settings → WordPress.")
    if not body.wp_password or not body.wp_password.strip():
        raise HTTPException(status_code=400, detail="No WordPress password. Go to Settings → WordPress.")

    result = run_full_pipeline(
        title=body.title,
        gemini_key=body.gemini_key.strip(),
        goapi_key=(body.goapi_key or "").strip(),
        wp_url=body.wp_url.strip(),
        wp_password=body.wp_password.strip(),
        publish_status=body.publish_status or "publish",
        mj_template=(body.mj_template or "").strip(),
        custom_prompt=(body.custom_prompt or "").strip(),
        card_prompt=(body.card_prompt or "").strip(),
        show_card=body.show_card if body.show_card is not None else True,
        use_images=body.use_images or False,
        use_pollinations=body.use_pollinations or False,
        pollinations_prompt=(body.pollinations_prompt or "").strip(),
        category_ids=body.category_ids,
        max_links=body.max_links or 4,
        use_internal_links=body.use_internal_links if body.use_internal_links is not None else True,
    )

    # Store body image bytes in memory cache for Pinterest pin image generation
    post_url = result.get("post_url", "")
    if post_url and result.get("body_images_bytes"):
        _article_image_cache[post_url] = result["body_images_bytes"]
        # Keep cache small — max 50 articles
        if len(_article_image_cache) > 50:
            oldest_key = next(iter(_article_image_cache))
            del _article_image_cache[oldest_key]

    # Save to DB if user is logged in
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ", 1)[1]
            user = supa_get_user(token)
            save_article_to_db(user["id"], token, body.title, result, body.publish_status or "publish")
        except Exception:
            pass

    return {
        "success": result.get("success", False),
        "post_url": result.get("post_url", ""),
        "post_id": result.get("post_id", ""),
        "featured_image_url": result.get("featured_image_url", ""),
        "error": result.get("error", "Unknown error"),
        "title": body.title,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  /generate — authenticated, reads settings from DB
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/generate")
def generate(body: GenerateRequest, auth=Depends(get_current_user)):
    user, token = auth
    user_id = user["id"]
    cfg = get_user_settings(user_id, token)
    if not cfg.get("gemini_key"): raise HTTPException(status_code=400, detail="No AI key configured.")
    if not cfg.get("wp_url"): raise HTTPException(status_code=400, detail="No WordPress URL configured.")

    results = []
    for title in body.titles:
        publish_status = "draft" if body.draft else cfg.get("publish_status", "publish")
        result = run_full_pipeline(
            title=title, gemini_key=cfg["gemini_key"], goapi_key=cfg.get("goapi_key",""),
            wp_url=cfg["wp_url"], wp_password=cfg["wp_password"], publish_status=publish_status,
            mj_template=cfg.get("mj_template",""), custom_prompt=cfg.get("custom_prompt",""),
            card_prompt=cfg.get("card_prompt",""), show_card=cfg.get("show_card",True),
            use_images=body.use_images, use_pollinations=cfg.get("use_pollinations",False),
            pollinations_prompt=cfg.get("pollinations_prompt",""), category_ids=body.category_ids,
            max_links=cfg.get("max_links",4), use_internal_links=cfg.get("use_internal_links",True),
        )

        # Cache body images for Pinterest
        post_url = result.get("post_url","")
        if post_url and result.get("body_images_bytes"):
            _article_image_cache[post_url] = result["body_images_bytes"]

        article_id = save_article_to_db(user_id, token, title, result, publish_status)
        results.append({
            "title": title, "success": result.get("success"),
            "post_url": result.get("post_url",""), "error": result.get("error",""),
            "article_id": article_id, "featured_image_url": result.get("featured_image_url",""),
        })

        plan = get_user_plan(user_id, token)
        if (plan == "pro" and cfg.get("auto_pin") and result.get("success")
                and cfg.get("pinterest_token") and cfg.get("pinterest_boards")):
            board_ids = [b.strip() for b in cfg["pinterest_boards"].split(",") if b.strip()]
            run_pinterest_bot(
                api_key=cfg["gemini_key"],
                access_token=cfg["pinterest_token"],
                articles=[{
                    "title": title,
                    "post_url": result.get("post_url",""),
                    "featured_image_url": result.get("featured_image_url",""),
                    "body_images_bytes": result.get("body_images_bytes", []),
                }],
                board_ids=board_ids,
                pinterest_prompt=cfg.get("pinterest_prompt",""),
                pin_delay_min=cfg.get("pin_delay_min",0),
                pin_image_prompt=cfg.get("pin_image_prompt",""),
                wp_url=cfg.get("wp_url",""),
                wp_password=cfg.get("wp_password",""),
            )

        delay = body.delay_sec or cfg.get("delay_sec",10)
        if delay > 0 and title != body.titles[-1]:
            time.sleep(delay)

    return {"results": results}


# ─────────────────────────────────────────────────────────────────────────────
#  PREVIEW
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/preview")
def preview(body: PreviewRequest, auth=Depends(get_current_user)):
    user, token = auth
    cfg = get_user_settings(user["id"], token)
    if not cfg.get("gemini_key"): raise HTTPException(status_code=400, detail="No AI key configured.")
    result = generate_article(body.title, cfg["gemini_key"], custom_prompt=cfg.get("custom_prompt",""))
    if result["success"]: return {"success":True,"content":result["content"],"seo_title":result["seo_title"]}
    raise HTTPException(status_code=500, detail=result["error"])


# ─────────────────────────────────────────────────────────────────────────────
#  HISTORY
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/history")
def get_history(auth=Depends(get_current_user)):
    user, token = auth
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/articles?user_id=eq.{user['id']}&order=created_at.desc&limit=200",
        headers=supa_headers(token), timeout=10)
    return {"articles": resp.json() if resp.status_code == 200 else []}


@app.delete("/history/{article_id}")
def delete_article(article_id: str, auth=Depends(get_current_user)):
    user, token = auth
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/articles?id=eq.{article_id}&user_id=eq.{user['id']}",
        headers=supa_headers(token), timeout=10)
    return {"success": resp.status_code in (200, 204)}


@app.delete("/history")
def clear_history(auth=Depends(get_current_user)):
    user, token = auth
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/articles?user_id=eq.{user['id']}",
        headers=supa_headers(token), timeout=10)
    return {"success": resp.status_code in (200, 204)}


# ─────────────────────────────────────────────────────────────────────────────
#  PINTEREST — PRO ONLY
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/pinterest/boards")
def pinterest_boards(auth=Depends(get_current_user)):
    user, token = auth
    plan = get_user_plan(user["id"], token)
    if plan != "pro": raise HTTPException(status_code=403, detail="Pinterest requires Pro plan.")
    cfg = get_user_settings(user["id"], token)
    if not cfg.get("pinterest_token"): raise HTTPException(status_code=400, detail="No Pinterest token in Settings.")
    return {"boards": get_pinterest_boards(cfg["pinterest_token"])}


@app.post("/pinterest/run")
def pinterest_run(body: PinterestRunRequest, auth=Depends(get_current_user)):
    user, token = auth
    plan = get_user_plan(user["id"], token)
    if plan != "pro": raise HTTPException(status_code=403, detail="Pinterest requires Pro plan.")
    cfg = get_user_settings(user["id"], token)
    if not cfg.get("pinterest_token"): raise HTTPException(status_code=400, detail="No Pinterest token.")
    if not cfg.get("gemini_key"): raise HTTPException(status_code=400, detail="No AI key.")

    # Fetch published articles from DB
    query = f"{SUPABASE_URL}/rest/v1/articles?user_id=eq.{user['id']}&status=eq.published"
    if body.article_ids:
        query += f"&id=in.({','.join(body.article_ids)})"
    art_resp = requests.get(query, headers=supa_headers(token), timeout=10)
    articles = art_resp.json() if art_resp.status_code == 200 else []
    if not articles:
        raise HTTPException(status_code=404, detail="No published articles found.")

    # Attach cached body image bytes to each article
    for art in articles:
        post_url = art.get("post_url", "")
        art["body_images_bytes"] = _article_image_cache.get(post_url, [])

    # Use pin_image_prompt from request body (sent by frontend) or fall back to settings
    pin_image_prompt = body.pin_image_prompt or cfg.get("pin_image_prompt", "")

    results = run_pinterest_bot(
        api_key=cfg["gemini_key"],
        access_token=cfg["pinterest_token"],
        articles=articles,
        board_ids=body.board_ids,
        pinterest_prompt=cfg.get("pinterest_prompt", ""),
        pin_delay_min=cfg.get("pin_delay_min", 0),
        pin_image_prompt=pin_image_prompt,
        wp_url=cfg.get("wp_url", ""),
        wp_password=cfg.get("wp_password", ""),
    )

    # Save pin results to DB
    for r in results:
        for br in r.get("boards", []):
            requests.post(
                f"{SUPABASE_URL}/rest/v1/pinterest_pins",
                headers=supa_headers(token),
                json={
                    "user_id": user["id"],
                    "pin_title": r.get("pin_title",""),
                    "pin_desc": r.get("pin_description",""),
                    "alt_text": r.get("alt_text",""),
                    "board_ids": br.get("board_id",""),
                    "pin_id": br.get("pin_id",""),
                    "status": "sent" if br.get("success") else "failed",
                    "error": br.get("error",""),
                },
                timeout=10,
            )

    return {"results": results}


# ─────────────────────────────────────────────────────────────────────────────
#  LEMONSQUEEZY WEBHOOK
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/checkout/basic")
def checkout_basic(auth=Depends(get_current_user)):
    user, token = auth
    email = user.get("email", "")
    base_url = os.getenv("LEMON_BASIC_URL", "")
    if not base_url:
        raise HTTPException(status_code=500, detail="Basic plan checkout not configured. Add LEMON_BASIC_URL to Railway env vars.")
    return {"url": f"{base_url}?checkout[email]={email}&checkout[custom][user_email]={email}"}


@app.get("/checkout/pro")
def checkout_pro(auth=Depends(get_current_user)):
    user, token = auth
    email = user.get("email", "")
    base_url = os.getenv("LEMON_PRO_URL", "")
    if not base_url:
        raise HTTPException(status_code=500, detail="Pro plan checkout not configured. Add LEMON_PRO_URL to Railway env vars.")
    return {"url": f"{base_url}?checkout[email]={email}&checkout[custom][user_email]={email}"}


@app.post("/webhook/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Signature", "")

    if LEMONSQUEEZY_SECRET:
        expected = hmac.new(LEMONSQUEEZY_SECRET.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("meta", {}).get("event_name", "")
    data = payload.get("data", {})
    attributes = data.get("attributes", {})

    user_email = (
        attributes.get("user_email") or
        attributes.get("order", {}).get("customer_email") or
        payload.get("meta", {}).get("custom_data", {}).get("user_email", "")
    )

    variant_id = str(
        attributes.get("variant_id", "") or
        attributes.get("first_order_item", {}).get("variant_id", "")
    )

    if not user_email:
        return {"status": "ignored", "reason": "no user email in payload"}

    if event in ("order_created", "subscription_created", "subscription_payment_success"):
        if variant_id == str(LEMON_PRO_VARIANT_ID) or "pro" in str(attributes.get("product_name","")).lower():
            plan = "pro"
        else:
            plan = "basic"
        success = upgrade_user_plan(user_email, plan)
        return {"status": "ok", "email": user_email, "plan": plan, "upgraded": success}

    elif event in ("subscription_cancelled", "subscription_expired"):
        success = upgrade_user_plan(user_email, "basic")
        return {"status": "ok", "email": user_email, "plan": "basic", "downgraded": success}

    return {"status": "ignored", "event": event}


# ─────────────────────────────────────────────────────────────────────────────
#  PROFILE
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/profile")
def get_profile(auth=Depends(get_current_user)):
    user, token = auth
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user['id']}&select=*",
        headers=supa_headers(token), timeout=10)
    rows = resp.json() if resp.status_code == 200 else []
    return {"profile": rows[0] if rows else {}}