# -*- coding: utf-8 -*-
"""
NicheFlow AI — generator.py
Handles: article generation, card generation, image generation, WordPress publishing,
         internal link injection, Pinterest bot
"""

import requests
import json
import base64
import re
import time
import io
import threading
from PIL import Image

# ─────────────────────────────────────────────────────────────────────────────
#  DEFAULT PROMPTS (used when user hasn't set a custom prompt)
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_ARTICLE_PROMPT = """You are a warm, expert content writer. Return ONLY a valid JSON object — no markdown, no preamble.

If the input topic is completely unrelated to any real content niche, return: {"error":"REJECTED"}

Pick a color theme based on topic type (use real hex values):
- Health/wellness/fitness      → MAIN:#16a34a, MAIN_DARK:#0d6b30, LIGHT_BG:#f0fdf4, BORDER:#86efac
- Food/recipes/cooking         → MAIN:#ea580c, MAIN_DARK:#b03a06, LIGHT_BG:#fff7ed, BORDER:#fdba74
- Pregnancy/baby/parenting     → MAIN:#db2777, MAIN_DARK:#9d174d, LIGHT_BG:#fdf2f8, BORDER:#f9a8d4
- Finance/business/money       → MAIN:#0369a1, MAIN_DARK:#075985, LIGHT_BG:#f0f9ff, BORDER:#7dd3fc
- Travel/lifestyle/adventure   → MAIN:#7c3aed, MAIN_DARK:#5b21b6, LIGHT_BG:#f5f3ff, BORDER:#c4b5fd
- Beauty/fashion/self-care     → MAIN:#d97706, MAIN_DARK:#b45309, LIGHT_BG:#fffbeb, BORDER:#fde68a
- Tech/software/AI             → MAIN:#0f766e, MAIN_DARK:#0d5c56, LIGHT_BG:#f0fdfa, BORDER:#5eead4
- General/other                → MAIN:#ea580c, MAIN_DARK:#b03a06, LIGHT_BG:#fff7ed, BORDER:#fdba74

Write html_content as a single-line string (\\n for newlines, \\" for quotes in HTML).
Replace MAIN/LIGHT_BG/BORDER/MAIN_DARK everywhere with actual hex values.

HTML structure:
<h1>[SEO-optimized title under 60 chars]</h1>
<p>[Hook — 3 engaging sentences that pull the reader in]</p>
<p>[Personal, relatable intro — why this topic matters — 3 sentences]</p>
<p>[What this article covers and what reader will gain — 3 sentences]</p>
<div style="text-align:center;margin:20px 0 25px 0;"><a style="background-color:MAIN;color:#fff;padding:12px 28px;border-radius:30px;font-weight:700;text-decoration:none;display:inline-block;" href="#main-section">Jump to Tips ✨</a></div>
##IMAGE1##
<h2>What Is {title} and Why Does It Matter?</h2>
<p>[Clear explanation — 3 sentences]</p>
<p>[Why people struggle with this — 3 sentences]</p>
<h2>Signs and Symptoms / What to Look For</h2>
<div style="background:LIGHT_BG;border-left:5px solid MAIN;border-radius:0 14px 14px 0;padding:20px 24px;box-shadow:0 2px 10px rgba(0,0,0,0.04);"><ul style="margin:0;padding-left:20px;line-height:2.6;"><li>[sign 1 — 2 full sentences with specific detail]</li><li>[sign 2 — 2 full sentences with specific detail]</li><li>[sign 3 — 2 full sentences with specific detail]</li><li>[sign 4 — 2 full sentences with specific detail]</li><li>[sign 5 — 2 full sentences with specific detail]</li></ul></div>
##IMAGE2##
<h2 id="main-section">[Core answer heading — directly answers what the title promises]</h2>
<p>[Specific, concrete answer — 3 full sentences with real detail]</p>
<p>[More depth — examples, steps, named techniques — 3 full sentences]</p>
<p>[Encouragement and what reader can expect — 3 sentences]</p>
<h2>Top Tips That Actually Work</h2>
<div style="background:LIGHT_BG;border-left:5px solid MAIN;border-radius:0 14px 14px 0;padding:20px 24px;box-shadow:0 2px 10px rgba(0,0,0,0.04);"><ul style="margin:0;padding-left:20px;line-height:2.6;"><li>[tip 1 with exact how-to — 2 full sentences]</li><li>[tip 2 with exact how-to — 2 full sentences]</li><li>[tip 3 with exact how-to — 2 full sentences]</li><li>[tip 4 with exact how-to — 2 full sentences]</li><li>[tip 5 with exact how-to — 2 full sentences]</li><li>[tip 6 with exact how-to — 2 full sentences]</li></ul></div>
<h2>Common Mistakes to Avoid</h2>
<p>[Mistake 1 + why it backfires + what to do instead — 3 sentences]</p>
<p>[Mistake 2 + what to do instead — 3 sentences]</p>
##IMAGE3##
<h2>When to Seek Professional Help</h2>
<p>[Specific warning signs — 3 sentences]</p>
<p>[Encouragement to advocate for yourself — 3 sentences]</p>
<h2>Frequently Asked Questions 🌸</h2>
<div style="border-left:4px solid BORDER;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px;background:LIGHT_BG;"><strong style="color:MAIN;font-size:16px;">[top googled question]</strong><p style="margin:10px 0 0;line-height:1.7;">[3 sentence answer]</p></div>
<div style="border-left:4px solid BORDER;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px;background:LIGHT_BG;"><strong style="color:MAIN;font-size:16px;">[second question]</strong><p style="margin:10px 0 0;line-height:1.7;">[3 sentence answer]</p></div>
<div style="border-left:4px solid BORDER;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px;background:LIGHT_BG;"><strong style="color:MAIN;font-size:16px;">[third question]</strong><p style="margin:10px 0 0;line-height:1.7;">[3 sentence answer]</p></div>
<div style="border-left:4px solid BORDER;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px;background:LIGHT_BG;"><strong style="color:MAIN;font-size:16px;">[fourth question]</strong><p style="margin:10px 0 0;line-height:1.7;">[3 sentence answer]</p></div>
<div style="border-left:4px solid BORDER;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px;background:LIGHT_BG;"><strong style="color:MAIN;font-size:16px;">[fifth question]</strong><p style="margin:10px 0 0;line-height:1.7;">[3 sentence answer]</p></div>
<p>[Warm 3-sentence closing — reader is seen, not alone, encouraged 🌸]</p>

WORD COUNT RULE: Must write at least 1000 words of visible text. Every paragraph = 3 full sentences minimum.

Return ONLY this JSON (no markdown):
{"seo_title":"","excerpt":"","html_content":"","MAIN":"","MAIN_DARK":"","LIGHT_BG":"","BORDER":""}

Topic: {title}"""


DEFAULT_CARD_PROMPT = """You are a structured data extractor. Return ONLY a valid JSON object — no markdown, no preamble.

For the topic "{title}", generate a helpful summary card:
- card_title: short display title (under 40 chars)
- card_type: type of card ("recipe" | "tips" | "checklist" | "comparison" | "guide")
- summary: 2-sentence summary of the topic
- key_points: array of 5 strings — the most important points
- quick_facts: array of objects with "label" and "value" keys (e.g. {"label":"Time","value":"15 mins"})
- cta_text: call-to-action text (e.g. "Save this for later!")

Return ONLY this JSON:
{"card_title":"","card_type":"","summary":"","key_points":[],"quick_facts":[],"cta_text":""}

Topic: {title}"""


DEFAULT_PINTEREST_PROMPT = """You are a Pinterest SEO expert. Return ONLY a valid JSON object — no markdown, no preamble.

For the article "{title}" published at {url}, create optimized Pinterest pin content:
- pin_title: max 60 chars, keyword-rich, use power words, no clickbait
- pin_description: max 150 chars, includes primary keyword, ends with CTA like "Save this!"
- alt_text: 1 descriptive sentence for accessibility and SEO
- hashtags: array of 5 relevant hashtags (without #)

Return ONLY this JSON:
{"pin_title":"","pin_description":"","alt_text":"","hashtags":[]}

Article title: {title}
Article URL: {url}"""


# ─────────────────────────────────────────────────────────────────────────────
#  AI API CALLS
# ─────────────────────────────────────────────────────────────────────────────

def _groq_call(api_key: str, prompt: str, prefer_fast: bool = False) -> str:
    if prefer_fast:
        model_order = ["llama-3.1-8b-instant", "gemma2-9b-it", "llama3-8b-8192"]
    else:
        model_order = [
            "llama-3.3-70b-versatile",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
        ]

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_err = None

    for model in model_order:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 8000,
                    "temperature": 0.7,
                },
                timeout=90,
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                if text and len(text.strip()) > 50:
                    return text
            elif resp.status_code == 429:
                last_err = "rate_limited"
                continue
            else:
                last_err = f"HTTP {resp.status_code}"
                continue
        except Exception as e:
            last_err = str(e)
            continue

    raise Exception(f"All Groq models failed. Last error: {last_err}")


def _gemini_call(api_key: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8000},
    }
    resp = requests.post(url, json=body, timeout=90)
    if resp.status_code == 200:
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise Exception("Gemini: no candidates (possible safety block)")
        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if text and len(text.strip()) > 50:
            return text
        raise Exception("Gemini returned empty text")
    elif resp.status_code == 429:
        raise Exception("Gemini quota exceeded")
    else:
        try:
            err = resp.json().get("error", {}).get("message", resp.text[:200])
        except Exception:
            err = resp.text[:200]
        raise Exception(f"Gemini error {resp.status_code}: {err}")


def ai_call(api_key: str, prompt: str, prefer_fast: bool = False) -> str:
    """
    Smart dispatcher: tries each key in comma-separated list.
    Groq keys start with gsk_, Gemini with AIza.
    Falls back automatically.
    """
    keys = [k.strip() for k in api_key.split(",") if k.strip()]
    last_err = None

    for key in keys:
        try:
            if key.startswith("gsk_"):
                return _groq_call(key, prompt, prefer_fast=prefer_fast)
            elif key.startswith("AIza"):
                return _gemini_call(key, prompt)
            else:
                last_err = f"Unrecognized key format: {key[:8]}..."
        except Exception as e:
            last_err = str(e)
            continue

    raise Exception(f"All AI keys failed. Last: {last_err}")


def parse_json_response(text: str) -> dict:
    """Extract JSON from AI response, handling markdown fences."""
    text = text.strip()
    # Remove markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    # Find first { to last }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]
    return json.loads(text)


# ─────────────────────────────────────────────────────────────────────────────
#  ARTICLE GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_article(title: str, api_key: str, custom_prompt: str = "", show_card: bool = True) -> dict:
    try:
        prompt_template = custom_prompt.strip() if custom_prompt.strip() else DEFAULT_ARTICLE_PROMPT
        prompt = prompt_template.replace("{title}", title)

        raw = ai_call(api_key, prompt, prefer_fast=False)

        try:
            parsed = parse_json_response(raw)
        except Exception:
            # Fallback: treat entire response as HTML content
            return {
                "success": True,
                "content": raw,
                "seo_title": title,
                "excerpt": "",
                "parsed": {},
            }

        if parsed.get("error") == "REJECTED":
            return {"success": False, "error": "Topic rejected by AI — not relevant to configured niche"}

        html = parsed.get("html_content", "")

        # Replace color placeholders
        for key in ["MAIN", "MAIN_DARK", "LIGHT_BG", "BORDER"]:
            val = parsed.get(key, "")
            if val:
                html = html.replace(key, val)

        return {
            "success": True,
            "content": html,
            "seo_title": parsed.get("seo_title", title),
            "excerpt": parsed.get("excerpt", ""),
            "parsed": parsed,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
#  CARD GENERATION (separate AI call)
# ─────────────────────────────────────────────────────────────────────────────

def generate_card(title: str, api_key: str, card_prompt: str = "", main_color: str = "#ea580c", light_bg: str = "#fff7ed", border_color: str = "#fdba74") -> str:
    """Returns HTML for the info card, or empty string on failure."""
    try:
        prompt_template = card_prompt.strip() if card_prompt.strip() else DEFAULT_CARD_PROMPT
        prompt = prompt_template.replace("{title}", title)

        raw = ai_call(api_key, prompt, prefer_fast=True)
        data = parse_json_response(raw)

        card_title = data.get("card_title", title)
        summary = data.get("summary", "")
        key_points = data.get("key_points", [])
        quick_facts = data.get("quick_facts", [])
        cta_text = data.get("cta_text", "Save this for later!")

        points_html = "".join(
            f'<li style="padding:6px 0;border-bottom:1px solid {border_color};line-height:1.5;">{p}</li>'
            for p in key_points
        )
        facts_html = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid {border_color};">'
            f'<span style="color:#666;font-size:13px;">{f.get("label","")}</span>'
            f'<span style="font-weight:600;font-size:13px;">{f.get("value","")}</span></div>'
            for f in quick_facts
        )

        html = f"""
<div id="summary-card" style="border:3px solid {main_color};border-radius:20px;padding:32px;background:linear-gradient(135deg,{light_bg} 0%,#ffffff 100%);box-shadow:0 8px 32px rgba(0,0,0,0.12);margin:32px 0;max-width:600px;">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
    <div style="background:{main_color};color:#fff;border-radius:12px;padding:8px 16px;font-weight:700;font-size:14px;">✦ Quick Summary</div>
    <h2 style="font-size:20px;font-weight:700;color:{main_color};margin:0;">{card_title}</h2>
  </div>
  {f'<p style="color:#555;line-height:1.7;margin-bottom:20px;font-size:15px;">{summary}</p>' if summary else ''}
  {f'<div style="margin-bottom:20px;"><div style="font-weight:700;font-size:14px;color:{main_color};margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">Key Points</div><ul style="list-style:none;padding:0;margin:0;">{points_html}</ul></div>' if points_html else ''}
  {f'<div style="margin-bottom:20px;"><div style="font-weight:700;font-size:14px;color:{main_color};margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">Quick Facts</div>{facts_html}</div>' if facts_html else ''}
  <div style="text-align:center;margin-top:20px;">
    <span style="background:{main_color};color:#fff;padding:10px 24px;border-radius:30px;font-weight:700;font-size:14px;display:inline-block;">{cta_text}</span>
  </div>
</div>"""
        return html

    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
#  META DESCRIPTION
# ─────────────────────────────────────────────────────────────────────────────

def generate_meta_description(title: str) -> str:
    words = title.lower().split()
    return f"Discover everything you need to know about {title}. Expert tips, practical advice, and real answers — read now."


# ─────────────────────────────────────────────────────────────────────────────
#  IMAGE GENERATION — GoAPI (Midjourney)
# ─────────────────────────────────────────────────────────────────────────────

def generate_midjourney_image(goapi_key: str, prompt: str, log_fn=None) -> dict:
    def log(msg):
        if log_fn:
            log_fn(msg)

    headers = {"x-api-key": goapi_key, "Content-Type": "application/json"}

    try:
        resp = requests.post(
            "https://api.goapi.ai/api/v1/task",
            headers=headers,
            json={"model": "midjourney", "task_type": "imagine", "input": {"prompt": prompt, "process_mode": "fast"}},
            timeout=30,
        )
        if resp.status_code != 200:
            return {"url": None, "error": f"MJ submit error: {resp.status_code}"}

        task_id = resp.json().get("data", {}).get("task_id")
        if not task_id:
            return {"url": None, "error": "No task_id returned"}

        log(f"  MJ task started: {task_id}")
        time.sleep(10)

        for attempt in range(90):
            time.sleep(3)
            poll = requests.get(f"https://api.goapi.ai/api/v1/task/{task_id}", headers=headers, timeout=15)
            if poll.status_code != 200:
                continue
            data = poll.json().get("data", {})
            status = data.get("status", "")

            if status == "completed":
                url = data.get("output", {}).get("image_urls", [None])[0]
                if url:
                    log(f"  ✓ MJ image ready")
                    return {"url": url, "error": None}
                return {"url": None, "error": "No image URL in completed response"}

            elif status == "failed":
                err = data.get("error", {}).get("message", "Unknown MJ error")
                # Retry in relax mode
                if "fast" in err.lower() or "quota" in err.lower():
                    log("  ⚠ Fast quota exhausted, retrying in relax mode...")
                    resp2 = requests.post(
                        "https://api.goapi.ai/api/v1/task",
                        headers=headers,
                        json={"model": "midjourney", "task_type": "imagine", "input": {"prompt": prompt, "process_mode": "relax"}},
                        timeout=30,
                    )
                    if resp2.status_code == 200:
                        task_id = resp2.json().get("data", {}).get("task_id", task_id)
                    continue
                return {"url": None, "error": err}

            elif attempt % 5 == 0:
                log(f"  ⏳ MJ generating... ({attempt * 3}s)")

        return {"url": None, "error": "Timeout after 270s"}

    except Exception as e:
        return {"url": None, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
#  IMAGE GENERATION — Pollinations (free, no key needed)
# ─────────────────────────────────────────────────────────────────────────────

def generate_pollinations_image(prompt: str, width: int = 1024, height: int = 1024) -> dict:
    try:
        safe_prompt = requests.utils.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={width}&height={height}&nologo=true"
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            return {"url": url, "raw_bytes": resp.content, "error": None}
        return {"url": None, "error": f"Pollinations error: {resp.status_code}"}
    except Exception as e:
        return {"url": None, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
#  IMAGE CONVERSION — to WebP
# ─────────────────────────────────────────────────────────────────────────────

def download_and_convert_webp(image_url: str, max_width: int = 1920) -> bytes | None:
    try:
        resp = requests.get(image_url, timeout=60, stream=True)
        if resp.status_code != 200:
            return None
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=80, method=1)
        return buf.getvalue()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  WORDPRESS HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def parse_wp_credentials(wp_url: str, wp_password: str):
    base_url = wp_url.rstrip("/")
    if ":" in wp_password:
        idx = wp_password.index(":")
        wp_user = wp_password[:idx].strip()
        wp_pass = wp_password[idx + 1:].strip()
    else:
        wp_user = ""
        wp_pass = wp_password.strip()
    return base_url, wp_user, wp_pass


def upload_image_to_wordpress(wp_url: str, wp_password: str, image_bytes: bytes, filename: str, log_fn=None) -> dict:
    def log(m):
        if log_fn:
            log_fn(m)

    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    if not wp_user:
        return {"success": False, "media_id": None, "url": None, "error": "No WP username"}

    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}", "Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/webp"}

    try:
        resp = requests.post(f"{base_url}/wp-json/wp/v2/media", headers=headers, data=image_bytes, timeout=60)
        if resp.status_code in (200, 201):
            data = resp.json()
            log(f"  ✓ Uploaded {filename}")
            return {"success": True, "media_id": data["id"], "url": data["source_url"], "error": None}
        return {"success": False, "media_id": None, "url": None, "error": f"WP upload error: {resp.status_code}"}
    except Exception as e:
        return {"success": False, "media_id": None, "url": None, "error": str(e)}


def publish_to_wordpress(
    title: str, content: str, wp_url: str, wp_password: str,
    status: str = "publish", meta_description: str = "",
    featured_media_id: int = None, category_ids: list = None,
) -> dict:
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    if not wp_user:
        return {"success": False, "error": "No WP username — format: username:password"}

    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

    payload = {"title": title, "content": content, "status": status}
    if featured_media_id:
        payload["featured_media"] = featured_media_id
    if category_ids:
        payload["categories"] = category_ids
    if meta_description:
        payload["meta"] = {"_yoast_wpseo_metadesc": meta_description}

    try:
        resp = requests.post(f"{base_url}/wp-json/wp/v2/posts", headers=headers, json=payload, timeout=60)
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"success": True, "post_id": data["id"], "post_url": data.get("link", ""), "error": None}
        try:
            err = resp.json().get("message", resp.text[:300])
        except Exception:
            err = resp.text[:300]
        return {"success": False, "error": f"WP error {resp.status_code}: {err}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_wp_categories(wp_url: str, wp_password: str) -> list:
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    try:
        resp = requests.get(f"{base_url}/wp-json/wp/v2/categories?per_page=100", headers=headers, timeout=15)
        if resp.status_code == 200:
            return [{"id": c["id"], "name": c["name"]} for c in resp.json()]
    except Exception:
        pass
    return []


def fetch_internal_links(wp_url: str, wp_password: str, max_posts: int = 200) -> list:
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    links = []
    page = 1
    while len(links) < max_posts:
        try:
            resp = requests.get(
                f"{base_url}/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=id,title,link",
                headers=headers, timeout=15,
            )
            if resp.status_code != 200:
                break
            posts = resp.json()
            if not posts:
                break
            for p in posts:
                links.append({"title": p["title"]["rendered"], "url": p["link"]})
            if len(posts) < 100:
                break
            page += 1
        except Exception:
            break
    return links


def inject_internal_links(html: str, links: list, current_title: str, max_links: int = 4, main_color: str = "#ea580c") -> str:
    if not links or not html:
        return html

    injected = 0
    used_urls = set()
    current_words = set(current_title.lower().split())

    for link in links:
        if injected >= max_links:
            break
        link_title = link.get("title", "")
        link_url = link.get("url", "")
        if not link_title or not link_url or link_url in used_urls:
            continue

        link_words = set(link_title.lower().split())
        common = current_words & link_words
        if len(common) > 0:
            continue  # Skip too-similar posts

        # Find the link title text in the HTML and wrap it
        if link_title in html:
            anchor = f'<a href="{link_url}" style="color:{main_color};text-decoration:underline;" title="{link_title}">{link_title}</a>'
            html = html.replace(link_title, anchor, 1)
            used_urls.add(link_url)
            injected += 1

    return html


# ─────────────────────────────────────────────────────────────────────────────
#  IMAGE INJECTION into article HTML
# ─────────────────────────────────────────────────────────────────────────────

def inject_images_into_article(html: str, image_results: list, title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    placeholders = ["##IMAGE1##", "##IMAGE2##", "##IMAGE3##"]

    # image_results[0] = featured (not in body), [1][2][3] = body images
    body_images = image_results[1:] if len(image_results) > 1 else []

    for i, ph in enumerate(placeholders):
        if ph not in html:
            continue
        img_data = body_images[i] if i < len(body_images) else None
        if img_data and img_data.get("url"):
            img_tag = (
                f'<figure style="margin:28px 0;text-align:center;">'
                f'<img src="{img_data["url"]}" alt="{title}" loading="lazy" '
                f'style="width:100%;max-width:720px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);" />'
                f"</figure>"
            )
            html = html.replace(ph, img_tag)
        else:
            html = html.replace(ph, "")

    return html


# ─────────────────────────────────────────────────────────────────────────────
#  PINTEREST BOT
# ─────────────────────────────────────────────────────────────────────────────

def generate_pin_content(
    api_key: str, title: str, article_url: str, pinterest_prompt: str = ""
) -> dict:
    """Use AI to generate optimized Pinterest pin content."""
    try:
        prompt_template = pinterest_prompt.strip() if pinterest_prompt.strip() else DEFAULT_PINTEREST_PROMPT
        prompt = prompt_template.replace("{title}", title).replace("{url}", article_url)

        raw = ai_call(api_key, prompt, prefer_fast=True)
        data = parse_json_response(raw)

        return {
            "success": True,
            "pin_title": data.get("pin_title", title[:60]),
            "pin_description": data.get("pin_description", ""),
            "alt_text": data.get("alt_text", title),
            "hashtags": data.get("hashtags", []),
        }
    except Exception as e:
        return {
            "success": False,
            "pin_title": title[:60],
            "pin_description": f"Check out this article: {article_url}",
            "alt_text": title,
            "hashtags": [],
            "error": str(e),
        }


def get_pinterest_boards(access_token: str) -> list:
    """Fetch user's Pinterest boards."""
    try:
        resp = requests.get(
            "https://api.pinterest.com/v5/boards",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"page_size": 50},
            timeout=15,
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            return [{"id": b["id"], "name": b["name"]} for b in items]
        return []
    except Exception:
        return []


def create_pinterest_pin(
    access_token: str,
    board_id: str,
    pin_title: str,
    pin_description: str,
    alt_text: str,
    article_url: str,
    image_url: str,
) -> dict:
    """Create a Pinterest pin via Pinterest API v5."""
    try:
        payload = {
            "board_id": board_id,
            "title": pin_title[:100],
            "description": pin_description[:500],
            "alt_text": alt_text[:500],
            "link": article_url,
            "media_source": {
                "source_type": "image_url",
                "url": image_url,
            },
        }
        resp = requests.post(
            "https://api.pinterest.com/v5/pins",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"success": True, "pin_id": data.get("id", ""), "error": None}
        err = resp.json().get("message", resp.text[:200])
        return {"success": False, "pin_id": None, "error": f"Pinterest API error: {err}"}
    except Exception as e:
        return {"success": False, "pin_id": None, "error": str(e)}


def run_pinterest_bot(
    api_key: str,
    access_token: str,
    articles: list,          # [{"title":..., "post_url":..., "featured_image_url":...}]
    board_ids: list,         # ["board_id_1", "board_id_2"]
    pinterest_prompt: str = "",
    pin_delay_min: int = 0,
    log_fn=None,
) -> list:
    """
    Full Pinterest automation pipeline.
    Returns list of results per article.
    """
    def log(msg):
        if log_fn:
            log_fn(msg)

    results = []

    for art in articles:
        title = art.get("title", "")
        url = art.get("post_url", "")
        featured_img = art.get("featured_image_url", "")

        log(f"📌 Processing: {title}")

        if not url:
            log("  ✗ No article URL — skipping")
            results.append({"title": title, "status": "failed", "error": "No article URL"})
            continue

        # Generate pin content with AI
        log("  ✦ Generating pin content with AI...")
        pin_data = generate_pin_content(api_key, title, url, pinterest_prompt)

        if not pin_data["success"]:
            log(f"  ⚠ AI generation failed, using fallback content")

        log(f"  ✓ Pin title: {pin_data['pin_title']}")

        if pin_delay_min > 0:
            log(f"  ⏱ Waiting {pin_delay_min} minute(s) before pinning...")
            time.sleep(pin_delay_min * 60)

        article_results = []
        for board_id in board_ids:
            log(f"  → Pinning to board {board_id}...")
            result = create_pinterest_pin(
                access_token=access_token,
                board_id=board_id,
                pin_title=pin_data["pin_title"],
                pin_description=pin_data["pin_description"],
                alt_text=pin_data["alt_text"],
                article_url=url,
                image_url=featured_img,
            )
            if result["success"]:
                log(f"  ✓ Pinned! ID: {result['pin_id']}")
            else:
                log(f"  ✗ Failed: {result['error']}")
            article_results.append({"board_id": board_id, **result})

        results.append({
            "title": title,
            "pin_title": pin_data["pin_title"],
            "pin_description": pin_data["pin_description"],
            "alt_text": pin_data["alt_text"],
            "boards": article_results,
            "status": "sent" if any(r["success"] for r in article_results) else "failed",
        })

    return results


# ─────────────────────────────────────────────────────────────────────────────
#  FULL PIPELINE — article + card + images + publish
# ─────────────────────────────────────────────────────────────────────────────

def run_full_pipeline(
    title: str,
    gemini_key: str,
    goapi_key: str = "",
    wp_url: str = "",
    wp_password: str = "",
    publish_status: str = "publish",
    mj_template: str = "",
    custom_prompt: str = "",
    card_prompt: str = "",
    show_card: bool = True,
    use_images: bool = True,
    use_pollinations: bool = False,
    pollinations_prompt: str = "",
    internal_links: list = None,
    category_ids: list = None,
    max_links: int = 4,
    use_internal_links: bool = True,
    log_fn=None,
) -> dict:

    def log(msg):
        if log_fn:
            log_fn(msg)

    art_result = [None]
    card_result = [None]
    image_results = [None, None, None, None]  # [featured, img1, img2, img3]
    all_threads = []
    _log_lock = threading.Lock()

    def safe_log(msg):
        with _log_lock:
            log(msg)

    # ── Thread 1: Article body ──────────────────────────────────────────────
    def _gen_article():
        safe_log("✏️ Generating article...")
        result = generate_article(title, gemini_key, custom_prompt=custom_prompt)
        art_result[0] = result
        if result["success"]:
            safe_log(f"✅ Article ready ({len(result['content'].split())} words)")
        else:
            safe_log(f"❌ Article failed: {result['error']}")

    # ── Thread 2: Card data ─────────────────────────────────────────────────
    def _gen_card():
        if not show_card:
            return
        safe_log("🃏 Generating summary card...")
        # Wait for article so we have color values
        deadline = time.time() + 120
        while art_result[0] is None and time.time() < deadline:
            time.sleep(1)
        main_color = "#ea580c"
        light_bg = "#fff7ed"
        border_color = "#fdba74"
        if art_result[0] and art_result[0].get("parsed"):
            p = art_result[0]["parsed"]
            main_color = p.get("MAIN", main_color)
            light_bg = p.get("LIGHT_BG", light_bg)
            border_color = p.get("BORDER", border_color)
        card_html = generate_card(title, gemini_key, card_prompt=card_prompt,
                                  main_color=main_color, light_bg=light_bg, border_color=border_color)
        card_result[0] = card_html
        if card_html:
            safe_log("✅ Card ready")
        else:
            safe_log("⚠️ Card generation failed (skipping)")

    # ── Thread 3: Images ────────────────────────────────────────────────────
    def _gen_images():
        if not use_images:
            return

        image_names = ["featured", "body-1", "body-2", "body-3"]
        image_threads = []

        def _gen_single(idx):
            img_prompt = ""
            if use_pollinations:
                tpl = pollinations_prompt or "Professional photography of {title}, editorial style, 4K"
                img_prompt = tpl.replace("{title}", title).replace("{recipe_name}", title)
                safe_log(f"  🖼️ Generating image {idx + 1}/4 (Pollinations)...")
                res = generate_pollinations_image(img_prompt)
                if res.get("url"):
                    if wp_url and wp_password:
                        webp = None
                        if res.get("raw_bytes"):
                            try:
                                img = Image.open(io.BytesIO(res["raw_bytes"])).convert("RGB")
                                buf = io.BytesIO()
                                img.save(buf, format="WEBP", quality=80)
                                webp = buf.getvalue()
                            except Exception:
                                pass
                        if webp:
                            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                            fname = f"{slug}-{image_names[idx]}.webp"
                            up = upload_image_to_wordpress(wp_url, wp_password, webp, fname, safe_log)
                            image_results[idx] = {"url": up.get("url"), "media_id": up.get("media_id")}
                            return
                    image_results[idx] = {"url": res["url"], "media_id": None}
                else:
                    safe_log(f"  ⚠️ Image {idx + 1} failed: {res.get('error')}")
                    image_results[idx] = {"url": None, "media_id": None}
            elif goapi_key:
                tpl = mj_template or "Professional photography of {recipe_name}, editorial style, natural light --ar 2:3"
                # Parse aspect ratio
                ar_match = re.search(r"--ar\s+(\d+:\d+)", tpl)
                ar = ar_match.group(1) if ar_match else "2:3"
                img_prompt = tpl.replace("{recipe_name}", title).replace("{title}", title)
                if "--ar" not in img_prompt:
                    img_prompt += f" --ar {ar}"

                safe_log(f"  🖼️ Generating image {idx + 1}/4 (Midjourney)...")
                res = generate_midjourney_image(goapi_key, img_prompt, safe_log)
                if res.get("url"):
                    webp = download_and_convert_webp(res["url"])
                    if webp and wp_url and wp_password:
                        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                        fname = f"{slug}-{image_names[idx]}.webp"
                        up = upload_image_to_wordpress(wp_url, wp_password, webp, fname, safe_log)
                        image_results[idx] = {"url": up.get("url"), "media_id": up.get("media_id")}
                    else:
                        image_results[idx] = {"url": res["url"], "media_id": None}
                else:
                    safe_log(f"  ⚠️ Image {idx + 1} failed: {res.get('error')}")
                    image_results[idx] = {"url": None, "media_id": None}

        for idx in range(4):
            t = threading.Thread(target=_gen_single, args=(idx,), daemon=True)
            image_threads.append(t)
            t.start()

        for t in image_threads:
            t.join(timeout=300)

    # ── Start all threads ────────────────────────────────────────────────────
    for fn in [_gen_article, _gen_card, _gen_images]:
        t = threading.Thread(target=fn, daemon=True)
        all_threads.append(t)
        t.start()

    # Wait
    deadline = time.time() + 600
    while any(t.is_alive() for t in all_threads):
        if time.time() > deadline:
            log("⚠️ Timeout after 10 minutes")
            break
        time.sleep(2)

    for t in all_threads:
        t.join(timeout=5)

    # ── Assemble result ──────────────────────────────────────────────────────
    art = art_result[0]
    if not art or not art["success"]:
        err = art["error"] if art else "Article thread failed"
        return {"success": False, "error": err}

    content = art["content"]

    # Inject images
    content = inject_images_into_article(content, image_results, title)

    # Append card
    if show_card and card_result[0]:
        content += card_result[0]

    # Inject internal links
    _links = internal_links
    if use_internal_links and not _links and wp_url and wp_password:
        log("🔗 Fetching internal links from WordPress...")
        try:
            _links = fetch_internal_links(wp_url, wp_password, max_posts=200)
            log(f"🔗 Loaded {len(_links)} posts")
        except Exception as e:
            log(f"⚠️ Could not fetch links: {e}")
    if _links:
        main_color = art.get("parsed", {}).get("MAIN", "#ea580c")
        content = inject_internal_links(content, _links, title, max_links=max_links, main_color=main_color)

    meta = generate_meta_description(title)
    wp_title = art.get("seo_title") or title

    log("📤 Publishing to WordPress...")
    featured_id = image_results[0]["media_id"] if image_results[0] and image_results[0].get("media_id") else None
    pub = publish_to_wordpress(
        title=wp_title, content=content, wp_url=wp_url, wp_password=wp_password,
        status=publish_status, meta_description=meta,
        featured_media_id=featured_id, category_ids=category_ids,
    )

    if pub["success"]:
        log(f"🎉 Published! → {pub.get('post_url', '')}")
        pub["featured_image_url"] = image_results[0].get("url") if image_results[0] else None
    else:
        log(f"❌ Publish failed: {pub['error']}")

    return pub


# ─────────────────────────────────────────────────────────────────────────────
#  TEST FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def test_gemini_key(api_key: str) -> dict:
    try:
        keys = [k.strip() for k in api_key.split(",") if k.strip()]
        for key in keys:
            if key.startswith("gsk_"):
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5},
                    timeout=15,
                )
                if resp.status_code == 200:
                    return {"success": True, "message": "✅ Groq key works! Ultra-fast — ready to go 🚀"}
                elif resp.status_code == 429:
                    return {"success": True, "message": "✅ Groq key valid (rate limited — wait 1 min)"}
                return {"success": False, "message": f"❌ Groq error: {resp.status_code}"}
            elif key.startswith("AIza"):
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
                resp = requests.post(url, json={"contents": [{"parts": [{"text": "Say OK"}]}], "generationConfig": {"maxOutputTokens": 5}}, timeout=15)
                if resp.status_code == 200:
                    return {"success": True, "message": "✅ Gemini key works!"}
                return {"success": False, "message": f"❌ Gemini error: {resp.status_code}"}
        return {"success": False, "message": "❌ Use gsk_ (Groq) or AIza (Gemini) key"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def test_goapi_key(api_key: str) -> dict:
    try:
        resp = requests.get("https://api.goapi.ai/api/v1/task", headers={"x-api-key": api_key}, timeout=10)
        return {"success": resp.status_code in (200, 405), "message": "✅ GoAPI key accepted" if resp.status_code in (200, 405) else "❌ Invalid GoAPI key"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def test_wordpress(wp_url: str, wp_password: str) -> dict:
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    if not wp_user:
        return {"success": False, "message": "❌ Format: username:password"}
    try:
        credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
        resp = requests.get(f"{base_url}/wp-json/wp/v2/users/me", headers={"Authorization": f"Basic {credentials}"}, timeout=10)
        if resp.status_code == 200:
            return {"success": True, "message": f"✅ Connected as: {resp.json().get('name', wp_user)}"}
        return {"success": False, "message": f"❌ HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def test_pinterest(access_token: str) -> dict:
    try:
        resp = requests.get(
            "https://api.pinterest.com/v5/user_account",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {"success": True, "message": f"✅ Pinterest connected as: {data.get('username', 'unknown')}"}
        return {"success": False, "message": f"❌ Pinterest error: {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
