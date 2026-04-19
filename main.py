# -*- coding: utf-8 -*-
"""
NicheFlow AI — main.py
FastAPI backend: auth proxy, settings CRUD, article pipeline, Pinterest bot
Deploy on Railway or Render (free tier)
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import requests
import os
import json

from generator import (
    run_full_pipeline,
    generate_article,
    generate_card,
    run_pinterest_bot,
    get_pinterest_boards,
    test_gemini_key,
    test_goapi_key,
    test_wordpress,
    test_pinterest,
    fetch_internal_links,
    fetch_wp_categories,
)

# ─────────────────────────────────────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────────────────────────────────────

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gfulpvqqpakcgubkilwc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_U9zJp_BBd-jkJCwvGimNmw_E4NyynFN")
SUPABASE_SECRET = os.getenv("SUPABASE_SECRET", "sb_secret_u_ZtMx7jmUBxXgOxhxYmaw_izKuJCyC")

app = FastAPI(title="NicheFlow AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
#  Supabase helpers
# ─────────────────────────────────────────────────────────────────────────────

def supa_headers(user_token: str = None):
    token = user_token or SUPABASE_KEY
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def supa_get_user(token: str) -> dict:
    resp = requests.get(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return resp.json()


def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = authorization.split(" ", 1)[1]
    return supa_get_user(token), token


def get_user_settings(user_id: str, token: str) -> dict:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/settings?user_id=eq.{user_id}&select=*",
        headers=supa_headers(token),
        timeout=10,
    )
    if resp.status_code == 200:
        rows = resp.json()
        return rows[0] if rows else {}
    return {}


def get_user_plan(user_id: str, token: str) -> str:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=plan",
        headers=supa_headers(token),
        timeout=10,
    )
    if resp.status_code == 200:
        rows = resp.json()
        return rows[0].get("plan", "basic") if rows else "basic"
    return "basic"


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


class GenerateRequest(BaseModel):
    titles: List[str]
    draft: Optional[bool] = False
    use_images: Optional[bool] = False
    delay_sec: Optional[int] = 10
    category_ids: Optional[List[int]] = None


class PreviewRequest(BaseModel):
    title: str


class TestRequest(BaseModel):
    key_type: str   # "ai" | "goapi" | "wp" | "pinterest"
    value: str
    wp_password: Optional[str] = ""


class PinterestRunRequest(BaseModel):
    article_ids: Optional[List[str]] = None   # Supabase article IDs; None = all published
    board_ids: List[str]


# ─────────────────────────────────────────────────────────────────────────────
#  AUTH ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/auth/signup")
def signup(body: dict):
    resp = requests.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": body["email"], "password": body["password"]},
        timeout=15,
    )
    data = resp.json()
    if resp.status_code in (200, 201):
        return {"success": True, "message": "Check your email to confirm your account."}
    raise HTTPException(status_code=400, detail=data.get("error_description", data.get("msg", "Signup failed")))


@app.post("/auth/login")
def login(body: dict):
    resp = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": body["email"], "password": body["password"]},
        timeout=15,
    )
    data = resp.json()
    if resp.status_code == 200:
        return {
            "success": True,
            "access_token": data["access_token"],
            "user": data["user"],
        }
    raise HTTPException(status_code=401, detail=data.get("error_description", "Login failed"))


# ─────────────────────────────────────────────────────────────────────────────
#  SETTINGS ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/settings")
def get_settings(auth=Depends(get_current_user)):
    user, token = auth
    user_id = user["id"]
    cfg = get_user_settings(user_id, token)
    plan = get_user_plan(user_id, token)
    return {"settings": cfg, "plan": plan}


@app.post("/settings")
def save_settings(body: SettingsUpdate, auth=Depends(get_current_user)):
    user, token = auth
    user_id = user["id"]

    data = body.dict()
    data["user_id"] = user_id
    data["updated_at"] = "now()"

    # Upsert
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/settings",
        headers={**supa_headers(token), "Prefer": "resolution=merge-duplicates,return=representation"},
        json=data,
        timeout=15,
    )
    if resp.status_code in (200, 201):
        return {"success": True}
    raise HTTPException(status_code=500, detail=f"Failed to save settings: {resp.text[:200]}")


# ─────────────────────────────────────────────────────────────────────────────
#  TEST ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/test")
def test_connection(body: TestRequest, auth=Depends(get_current_user)):
    if body.key_type == "ai":
        return test_gemini_key(body.value)
    elif body.key_type == "goapi":
        return test_goapi_key(body.value)
    elif body.key_type == "wp":
        return test_wordpress(body.value, body.wp_password or "")
    elif body.key_type == "pinterest":
        return test_pinterest(body.value)
    raise HTTPException(status_code=400, detail="Unknown key_type")


# ─────────────────────────────────────────────────────────────────────────────
#  WORDPRESS HELPERS ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/wp/categories")
def wp_categories(auth=Depends(get_current_user)):
    user, token = auth
    cfg = get_user_settings(user["id"], token)
    cats = fetch_wp_categories(cfg.get("wp_url", ""), cfg.get("wp_password", ""))
    return {"categories": cats}


@app.get("/wp/posts")
def wp_posts(auth=Depends(get_current_user)):
    user, token = auth
    cfg = get_user_settings(user["id"], token)
    posts = fetch_internal_links(cfg.get("wp_url", ""), cfg.get("wp_password", ""), max_posts=200)
    return {"posts": posts}


# ─────────────────────────────────────────────────────────────────────────────
#  GENERATE ROUTE
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/generate")
def generate(body: GenerateRequest, auth=Depends(get_current_user)):
    user, token = auth
    user_id = user["id"]
    cfg = get_user_settings(user_id, token)

    if not cfg.get("gemini_key"):
        raise HTTPException(status_code=400, detail="No AI key configured. Go to Settings.")
    if not cfg.get("wp_url"):
        raise HTTPException(status_code=400, detail="No WordPress URL configured. Go to Settings.")

    results = []

    for title in body.titles:
        publish_status = "draft" if body.draft else cfg.get("publish_status", "publish")

        result = run_full_pipeline(
            title=title,
            gemini_key=cfg["gemini_key"],
            goapi_key=cfg.get("goapi_key", ""),
            wp_url=cfg["wp_url"],
            wp_password=cfg["wp_password"],
            publish_status=publish_status,
            mj_template=cfg.get("mj_template", ""),
            custom_prompt=cfg.get("custom_prompt", ""),
            card_prompt=cfg.get("card_prompt", ""),
            show_card=cfg.get("show_card", True),
            use_images=body.use_images,
            use_pollinations=cfg.get("use_pollinations", False),
            pollinations_prompt=cfg.get("pollinations_prompt", ""),
            category_ids=body.category_ids,
            max_links=cfg.get("max_links", 4),
            use_internal_links=cfg.get("use_internal_links", True),
        )

        # Save to Supabase articles table
        article_data = {
            "user_id": user_id,
            "title": title,
            "post_url": result.get("post_url", ""),
            "post_id": str(result.get("post_id", "")),
            "status": "published" if result.get("success") else "failed",
            "wp_status": publish_status,
            "error": result.get("error", ""),
        }
        db_resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/articles",
            headers=supa_headers(token),
            json=article_data,
            timeout=10,
        )
        article_id = None
        if db_resp.status_code in (200, 201):
            rows = db_resp.json()
            article_id = rows[0]["id"] if rows else None

        results.append({
            "title": title,
            "success": result.get("success"),
            "post_url": result.get("post_url", ""),
            "error": result.get("error", ""),
            "article_id": article_id,
            "featured_image_url": result.get("featured_image_url", ""),
        })

        # Auto-pin if Pro and enabled
        plan = get_user_plan(user_id, token)
        if (plan == "pro" and cfg.get("auto_pin") and
                result.get("success") and cfg.get("pinterest_token") and
                cfg.get("pinterest_boards")):
            board_ids = [b.strip() for b in cfg["pinterest_boards"].split(",") if b.strip()]
            run_pinterest_bot(
                api_key=cfg["gemini_key"],
                access_token=cfg["pinterest_token"],
                articles=[{
                    "title": title,
                    "post_url": result.get("post_url", ""),
                    "featured_image_url": result.get("featured_image_url", ""),
                }],
                board_ids=board_ids,
                pinterest_prompt=cfg.get("pinterest_prompt", ""),
                pin_delay_min=cfg.get("pin_delay_min", 0),
            )

        # Delay between articles
        delay = body.delay_sec or cfg.get("delay_sec", 10)
        if delay > 0 and title != body.titles[-1]:
            import time
            time.sleep(delay)

    return {"results": results}


# ─────────────────────────────────────────────────────────────────────────────
#  PREVIEW ROUTE
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/preview")
def preview(body: PreviewRequest, auth=Depends(get_current_user)):
    user, token = auth
    cfg = get_user_settings(user["id"], token)
    if not cfg.get("gemini_key"):
        raise HTTPException(status_code=400, detail="No AI key configured.")
    result = generate_article(body.title, cfg["gemini_key"], custom_prompt=cfg.get("custom_prompt", ""))
    if result["success"]:
        return {"success": True, "content": result["content"], "seo_title": result["seo_title"]}
    raise HTTPException(status_code=500, detail=result["error"])


# ─────────────────────────────────────────────────────────────────────────────
#  HISTORY ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/history")
def get_history(auth=Depends(get_current_user)):
    user, token = auth
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/articles?user_id=eq.{user['id']}&order=created_at.desc&limit=200",
        headers=supa_headers(token),
        timeout=10,
    )
    if resp.status_code == 200:
        return {"articles": resp.json()}
    return {"articles": []}


@app.delete("/history/{article_id}")
def delete_article(article_id: str, auth=Depends(get_current_user)):
    user, token = auth
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/articles?id=eq.{article_id}&user_id=eq.{user['id']}",
        headers=supa_headers(token),
        timeout=10,
    )
    return {"success": resp.status_code in (200, 204)}


@app.delete("/history")
def clear_history(auth=Depends(get_current_user)):
    user, token = auth
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/articles?user_id=eq.{user['id']}",
        headers=supa_headers(token),
        timeout=10,
    )
    return {"success": resp.status_code in (200, 204)}


# ─────────────────────────────────────────────────────────────────────────────
#  PINTEREST ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/pinterest/boards")
def pinterest_boards(auth=Depends(get_current_user)):
    user, token = auth
    cfg = get_user_settings(user["id"], token)
    plan = get_user_plan(user["id"], token)
    if plan != "pro":
        raise HTTPException(status_code=403, detail="Pinterest is a Pro feature")
    boards = get_pinterest_boards(cfg.get("pinterest_token", ""))
    return {"boards": boards}


@app.post("/pinterest/run")
def pinterest_run(body: PinterestRunRequest, auth=Depends(get_current_user)):
    user, token = auth
    cfg = get_user_settings(user["id"], token)
    plan = get_user_plan(user["id"], token)
    if plan != "pro":
        raise HTTPException(status_code=403, detail="Pinterest is a Pro feature")
    if not cfg.get("pinterest_token"):
        raise HTTPException(status_code=400, detail="No Pinterest token configured")

    # Fetch articles from Supabase
    query = f"{SUPABASE_URL}/rest/v1/articles?user_id=eq.{user['id']}&status=eq.published"
    if body.article_ids:
        ids = ",".join(body.article_ids)
        query += f"&id=in.({ids})"
    art_resp = requests.get(query, headers=supa_headers(token), timeout=10)
    articles = art_resp.json() if art_resp.status_code == 200 else []

    if not articles:
        raise HTTPException(status_code=404, detail="No published articles found")

    results = run_pinterest_bot(
        api_key=cfg["gemini_key"],
        access_token=cfg["pinterest_token"],
        articles=articles,
        board_ids=body.board_ids,
        pinterest_prompt=cfg.get("pinterest_prompt", ""),
        pin_delay_min=cfg.get("pin_delay_min", 0),
    )

    # Save pins to Supabase
    for r in results:
        for board_result in r.get("boards", []):
            pin_data = {
                "user_id": user["id"],
                "pin_title": r.get("pin_title", ""),
                "pin_desc": r.get("pin_description", ""),
                "alt_text": r.get("alt_text", ""),
                "board_ids": board_result.get("board_id", ""),
                "pin_id": board_result.get("pin_id", ""),
                "status": "sent" if board_result.get("success") else "failed",
                "error": board_result.get("error", ""),
            }
            requests.post(
                f"{SUPABASE_URL}/rest/v1/pinterest_pins",
                headers=supa_headers(token),
                json=pin_data,
                timeout=10,
            )

    return {"results": results}


# ─────────────────────────────────────────────────────────────────────────────
#  PROFILE / PLAN
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/profile")
def get_profile(auth=Depends(get_current_user)):
    user, token = auth
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user['id']}&select=*",
        headers=supa_headers(token),
        timeout=10,
    )
    if resp.status_code == 200:
        rows = resp.json()
        return {"profile": rows[0] if rows else {}}
    return {"profile": {}}
@app.post("/generate-proxy")
async def generate_proxy(body: dict, auth=Depends(get_current_user)):
    user, token = auth
    cfg = get_user_settings(user["id"], token)
    if not cfg.get("gemini_key"):
        raise HTTPException(status_code=400, detail="No AI key configured")
    from generator import ai_call
    result = ai_call(cfg["gemini_key"], body.get("userMessage", ""))
    return {"text": result}


@app.get("/health")
def health():
    return {"status": "ok", "service": "NicheFlow AI"}
