# -*- coding: utf-8 -*-
"""NicheFlow AI — generator.py"""
import requests, json, base64, re, time, io, threading
from PIL import Image, ImageDraw, ImageFont

DEFAULT_ARTICLE_PROMPT = """You are a warm expert content writer. Return ONLY a valid JSON object, no markdown, no preamble.
If topic unrelated to any content niche return: {"error":"REJECTED"}
Pick color theme (use real hex):
Food/recipes → MAIN:#ea580c,MAIN_DARK:#b03a06,LIGHT_BG:#fff7ed,BORDER:#fdba74
Pregnancy/baby → MAIN:#db2777,MAIN_DARK:#9d174d,LIGHT_BG:#fdf2f8,BORDER:#f9a8d4
Health/fitness → MAIN:#16a34a,MAIN_DARK:#0d6b30,LIGHT_BG:#f0fdf4,BORDER:#86efac
Finance → MAIN:#0369a1,MAIN_DARK:#075985,LIGHT_BG:#f0f9ff,BORDER:#7dd3fc
Travel → MAIN:#7c3aed,MAIN_DARK:#5b21b6,LIGHT_BG:#f5f3ff,BORDER:#c4b5fd
Beauty → MAIN:#d97706,MAIN_DARK:#b45309,LIGHT_BG:#fffbeb,BORDER:#fde68a
Tech → MAIN:#0f766e,MAIN_DARK:#0d5c56,LIGHT_BG:#f0fdfa,BORDER:#5eead4
General → MAIN:#ea580c,MAIN_DARK:#b03a06,LIGHT_BG:#fff7ed,BORDER:#fdba74

Write html_content as SINGLE LINE string. Include ##IMAGE1## ##IMAGE2## ##IMAGE3## placeholders. Replace MAIN/LIGHT_BG/BORDER/MAIN_DARK with hex values. Minimum 1000 words visible text. Every paragraph 3 sentences. Every bullet 2 sentences.

Return ONLY this JSON (no markdown):
{"seo_title":"[under 60 chars]","excerpt":"[2 sentence summary]","html_content":"[full article HTML single line]","MAIN":"#hex","MAIN_DARK":"#hex","LIGHT_BG":"#hex","BORDER":"#hex"}

The html_content structure (replace color names with hex values, use \\" for quotes inside string):
<h1>[title]</h1><p>[Hook 3 sentences]</p><p>[Personal intro 3 sentences]</p><p>[What article covers, end with: This is one of those things I wish someone had told me sooner.]</p><div style=\\"text-align:center;margin:20px 0;\\"><a style=\\"background-color:MAIN;color:#fff;padding:12px 28px;border-radius:30px;font-weight:700;text-decoration:none;display:inline-block;\\" href=\\"#tips\\">Jump to Tips</a></div>##IMAGE1##<h2>What Is {title} and Why It Matters</h2><p>[3 sentences]</p><p>[3 sentences]</p><h2>Signs You Need This</h2><div style=\\"background:LIGHT_BG;border-left:5px solid MAIN;border-radius:0 14px 14px 0;padding:20px 24px;\\"><ul style=\\"margin:0;padding-left:20px;line-height:2.6;\\"><li>[2 sentences]</li><li>[2 sentences]</li><li>[2 sentences]</li><li>[2 sentences]</li><li>[2 sentences]</li></ul></div>##IMAGE2##<h2 id=\\"tips\\">[Answer heading]</h2><p>[3 sentences]</p><p>[3 sentences]</p><p>[3 sentences]</p><h2>Top Tips</h2><div style=\\"background:LIGHT_BG;border-left:5px solid MAIN;border-radius:0 14px 14px 0;padding:20px 24px;\\"><ul style=\\"margin:0;padding-left:20px;line-height:2.6;\\"><li>[2 sentences]</li><li>[2 sentences]</li><li>[2 sentences]</li><li>[2 sentences]</li><li>[2 sentences]</li><li>[2 sentences]</li></ul></div><h2>Mistakes to Avoid</h2><p>[3 sentences]</p><p>[3 sentences]</p>##IMAGE3##<h2>When to Seek Help</h2><p>[3 sentences]</p><p>[3 sentences]</p><h2>Frequently Asked Questions</h2><div style=\\"border-left:4px solid BORDER;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px;background:LIGHT_BG;\\"><strong style=\\"color:MAIN;font-size:16px;\\">[Q1]</strong><p style=\\"margin:10px 0 0;line-height:1.7;\\">[3 sentence answer]</p></div><div style=\\"border-left:4px solid BORDER;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px;background:LIGHT_BG;\\"><strong style=\\"color:MAIN;font-size:16px;\\">[Q2]</strong><p style=\\"margin:10px 0 0;line-height:1.7;\\">[3 sentence answer]</p></div><div style=\\"border-left:4px solid BORDER;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px;background:LIGHT_BG;\\"><strong style=\\"color:MAIN;font-size:16px;\\">[Q3]</strong><p style=\\"margin:10px 0 0;line-height:1.7;\\">[3 sentence answer]</p></div><div style=\\"border-left:4px solid BORDER;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px;background:LIGHT_BG;\\"><strong style=\\"color:MAIN;font-size:16px;\\">[Q4]</strong><p style=\\"margin:10px 0 0;line-height:1.7;\\">[3 sentence answer]</p></div><div style=\\"border-left:4px solid BORDER;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px;background:LIGHT_BG;\\"><strong style=\\"color:MAIN;font-size:16px;\\">[Q5]</strong><p style=\\"margin:10px 0 0;line-height:1.7;\\">[3 sentence answer]</p></div><p>[Warm closing 3 sentences]</p>

Topic: {title}"""

DEFAULT_CARD_PROMPT = """Return ONLY valid JSON, no markdown.
For "{title}" generate a summary card:
{"card_title":"[under 40 chars]","card_type":"recipe|tips|checklist|comparison|guide","summary":"[2 sentences]","key_points":["point 1","point 2","point 3","point 4","point 5"],"quick_facts":[{"label":"Time","value":"15 mins"}],"cta_text":"Save this! 📌"}
Topic: {title}"""

DEFAULT_PINTEREST_PROMPT = """Return ONLY valid JSON, no markdown.
For article "{title}" at {url}:
{"pin_title":"[max 60 chars keyword-rich]","pin_description":"[max 150 chars with CTA Save this!]","alt_text":"[1 descriptive sentence]","hashtags":["tag1","tag2","tag3","tag4","tag5"]}"""

HOOK_TITLE_PROMPT = """Return ONLY a JSON object, no markdown, no explanation.
Generate a compelling 4-word Pinterest hook title for an article about "{title}".
The hook must be EXACTLY 4 words, catchy, emotional, and perfect for a Pinterest pin image.
Example format: {{"hook":"Must Try This Now"}}
Return only: {{"hook":"[exactly 4 words]"}}
Topic: {title}"""


# ─── AI Calls ────────────────────────────────────────────────────────────────

def _groq_call(api_key, prompt, prefer_fast=False):
    models = ["llama-3.1-8b-instant", "gemma2-9b-it"] if prefer_fast else [
        "llama-3.3-70b-versatile", "meta-llama/llama-4-scout-17b-16e-instruct",
        "llama-3.1-70b-versatile", "llama-3.1-8b-instant"
    ]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_err = None
    for model in models:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions", headers=headers,
                json={"model": model, "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 8000, "temperature": 0.7}, timeout=90)
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
    raise Exception(f"All Groq models failed: {last_err}")


def _gemini_call(api_key, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    resp = requests.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8000}
    }, timeout=90)
    if resp.status_code == 200:
        candidates = resp.json().get("candidates", [])
        if not candidates:
            raise Exception("Gemini: no candidates")
        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if text and len(text.strip()) > 50:
            return text
        raise Exception("Gemini empty text")
    elif resp.status_code == 429:
        raise Exception("Gemini quota exceeded")
    else:
        try:
            err = resp.json().get("error", {}).get("message", resp.text[:200])
        except:
            err = resp.text[:200]
        raise Exception(f"Gemini {resp.status_code}: {err}")


def ai_call(api_key, prompt, prefer_fast=False):
    keys = [k.strip() for k in api_key.split(",") if k.strip()]
    last_err = None
    for key in keys:
        try:
            if key.startswith("gsk_"):
                return _groq_call(key, prompt, prefer_fast)
            elif key.startswith("AIza"):
                return _gemini_call(key, prompt)
            else:
                last_err = f"Unknown key format: {key[:8]}"
        except Exception as e:
            last_err = str(e)
            continue
    raise Exception(f"All AI keys failed: {last_err}")


def parse_json_response(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]
    return json.loads(text)


# ─── Article & Card ──────────────────────────────────────────────────────────

def generate_article(title, api_key, custom_prompt="", show_card=True):
    try:
        prompt = (custom_prompt.strip() if custom_prompt.strip() else DEFAULT_ARTICLE_PROMPT).replace("{title}", title)
        raw = ai_call(api_key, prompt, prefer_fast=False)
        try:
            parsed = parse_json_response(raw)
        except:
            return {"success": True, "content": raw, "seo_title": title, "excerpt": "", "parsed": {}}
        if parsed.get("error") == "REJECTED":
            return {"success": False, "error": "Topic rejected"}
        html = parsed.get("html_content", "")
        if not html:
            return {"success": False, "error": "Empty html_content"}
        for key in ["MAIN", "MAIN_DARK", "LIGHT_BG", "BORDER"]:
            val = parsed.get(key, "")
            if val:
                html = html.replace(key, val)
        return {"success": True, "content": html, "seo_title": parsed.get("seo_title", title),
                "excerpt": parsed.get("excerpt", ""), "parsed": parsed}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_card(title, api_key, card_prompt="", main_color="#ea580c", light_bg="#fff7ed", border_color="#fdba74"):
    """Generate summary card with a FULLY CLICKABLE CTA button."""
    try:
        prompt = (card_prompt.strip() if card_prompt.strip() else DEFAULT_CARD_PROMPT).replace("{title}", title)
        raw = ai_call(api_key, prompt, prefer_fast=True)
        data = parse_json_response(raw)
        card_title = data.get("card_title", title)
        summary = data.get("summary", "")
        key_points = data.get("key_points", [])
        quick_facts = data.get("quick_facts", [])
        cta_text = data.get("cta_text", "Save this! 📌")

        points_html = "".join(
            f'<li style="padding:8px 0;border-bottom:1px solid {border_color};line-height:1.6;'
            f'display:flex;align-items:flex-start;gap:8px;">'
            f'<span style="color:{main_color};font-weight:700;flex-shrink:0;margin-top:2px;">✓</span>'
            f'<span>{p}</span></li>'
            for p in key_points
        )
        facts_html = "".join(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:8px 0;border-bottom:1px solid {border_color};">'
            f'<span style="color:#666;font-size:13px;">{f.get("label","")}</span>'
            f'<span style="font-weight:700;font-size:14px;color:{main_color};">{f.get("value","")}</span></div>'
            for f in quick_facts
        )

        cta_js = (
            "if(navigator.share){"
            "navigator.share({title:document.title,url:window.location.href})"
            ".catch(function(){});"
            "}else if(navigator.clipboard){"
            "navigator.clipboard.writeText(window.location.href);"
            "var b=this;var t=b.innerText;b.innerText='Copied!';setTimeout(function(){b.innerText=t;},2000);"
            "}else{"
            "prompt('Copy this link:',window.location.href);"
            "}"
            "return false;"
        )

        return (
            f'<div id="nicheflow-card" style="border:3px solid {main_color};border-radius:20px;padding:32px;'
            f'background:linear-gradient(135deg,{light_bg} 0%,#ffffff 100%);'
            f'box-shadow:0 8px 32px rgba(0,0,0,0.12);margin:32px 0;max-width:640px;'
            f'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Helvetica,Arial,sans-serif;">'
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;flex-wrap:wrap;">'
            f'<div style="background:{main_color};color:#fff;border-radius:12px;padding:6px 16px;'
            f'font-weight:700;font-size:12px;letter-spacing:0.5px;text-transform:uppercase;">✦ Quick Summary</div>'
            f'<span style="font-size:17px;font-weight:700;color:{main_color};">{card_title}</span>'
            f'</div>'
            + (f'<p style="color:#444;line-height:1.7;margin-bottom:20px;font-size:15px;'
               f'border-left:3px solid {main_color};padding-left:12px;">{summary}</p>' if summary else '')
            + (f'<div style="margin-bottom:20px;">'
               f'<div style="font-weight:700;font-size:11px;color:{main_color};margin-bottom:10px;'
               f'text-transform:uppercase;letter-spacing:1px;">Key Points</div>'
               f'<ul style="list-style:none;padding:0;margin:0;">{points_html}</ul>'
               f'</div>' if points_html else '')
            + (f'<div style="margin-bottom:20px;">'
               f'<div style="font-weight:700;font-size:11px;color:{main_color};margin-bottom:10px;'
               f'text-transform:uppercase;letter-spacing:1px;">Quick Facts</div>'
               f'{facts_html}</div>' if facts_html else '')
            + f'<div style="text-align:center;margin-top:24px;">'
            f'<button onclick="{cta_js}" '
            f'style="background:{main_color};color:#fff;padding:13px 30px;border-radius:30px;'
            f'font-weight:700;font-size:14px;border:none;cursor:pointer;'
            f'box-shadow:0 4px 14px rgba(0,0,0,0.15);transition:opacity 0.2s;"'
            f'onmouseover="this.style.opacity=\'0.88\'" onmouseout="this.style.opacity=\'1\'">'
            f'{cta_text}</button></div>'
            f'</div>'
        )
    except Exception:
        cta_js = "if(navigator.share){navigator.share({title:document.title,url:window.location.href}).catch(function(){});}else{navigator.clipboard&&navigator.clipboard.writeText(window.location.href);}return false;"
        return (
            f'<div id="nicheflow-card" style="border:2px solid {main_color};border-radius:16px;'
            f'padding:24px;background:{light_bg};margin:24px 0;'
            f'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif;">'
            f'<div style="font-weight:700;color:{main_color};margin-bottom:8px;">✦ Quick Summary</div>'
            f'<p style="color:#555;line-height:1.6;margin-bottom:16px;">{title}</p>'
            f'<div style="text-align:center;">'
            f'<button onclick="{cta_js}" '
            f'style="background:{main_color};color:#fff;padding:10px 24px;border-radius:20px;'
            f'font-size:13px;font-weight:600;border:none;cursor:pointer;">Save this! 📌</button>'
            f'</div></div>'
        )


def generate_meta_description(title):
    return f"Discover everything about {title}. Expert tips, practical advice, and real answers — read now!"


# ─── Image Generation ─────────────────────────────────────────────────────────

def generate_midjourney_image(goapi_key, prompt, log_fn=None):
    def log(m):
        if log_fn: log_fn(m)
    headers = {"x-api-key": goapi_key, "Content-Type": "application/json"}
    try:
        resp = requests.post("https://api.goapi.ai/api/v1/task", headers=headers,
                             json={"model": "midjourney", "task_type": "imagine",
                                   "input": {"prompt": prompt, "process_mode": "fast"}}, timeout=30)
        if resp.status_code != 200:
            return {"url": None, "error": f"MJ error {resp.status_code}"}
        task_id = resp.json().get("data", {}).get("task_id")
        if not task_id:
            return {"url": None, "error": "No task_id"}
        log(f"  🎨 MJ task: {task_id}")
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
                    log("  ✅ MJ ready")
                    return {"url": url, "error": None}
                return {"url": None, "error": "No image URL"}
            elif status == "failed":
                err = data.get("error", {}).get("message", "Unknown")
                if "fast" in err.lower() or "quota" in err.lower():
                    log("  ⚠️ Fast quota, trying relax...")
                    resp2 = requests.post("https://api.goapi.ai/api/v1/task", headers=headers,
                                          json={"model": "midjourney", "task_type": "imagine",
                                                "input": {"prompt": prompt, "process_mode": "relax"}}, timeout=30)
                    if resp2.status_code == 200:
                        task_id = resp2.json().get("data", {}).get("task_id", task_id)
                    continue
                return {"url": None, "error": err}
            elif attempt % 5 == 0:
                log(f"  ⏳ Generating... ({attempt * 3}s)")
        return {"url": None, "error": "Timeout 270s"}
    except Exception as e:
        return {"url": None, "error": str(e)}


def generate_pollinations_image(prompt, width=1024, height=1024):
    try:
        safe_prompt = requests.utils.quote(prompt[:400])
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={width}&height={height}&nologo=true&seed={int(time.time())}"
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            return {"url": url, "raw_bytes": resp.content, "error": None}
        return {"url": None, "error": f"Pollinations {resp.status_code}"}
    except Exception as e:
        return {"url": None, "error": str(e)}


def download_and_convert_webp(image_url, max_width=1920):
    """Download image from URL, convert to WebP, return bytes."""
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


def bytes_to_webp(raw_bytes, max_width=1920):
    """Convert raw image bytes to WebP bytes."""
    try:
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=80, method=1)
        return buf.getvalue()
    except Exception:
        return None


# ─── WordPress ───────────────────────────────────────────────────────────────

def parse_wp_credentials(wp_url, wp_password):
    base_url = wp_url.rstrip("/")
    if ":" in wp_password:
        idx = wp_password.index(":")
        wp_user = wp_password[:idx].strip()
        wp_pass = wp_password[idx + 1:].strip()
    else:
        wp_user = ""
        wp_pass = wp_password.strip()
    return base_url, wp_user, wp_pass


def upload_image_to_wordpress(wp_url, wp_password, image_bytes, filename, log_fn=None):
    """Upload WebP bytes to WP media library. Returns dict with media_id and url."""
    def log(m):
        if log_fn: log_fn(m)

    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    if not wp_user:
        log("  ⚠️ No WP username in credentials")
        return {"success": False, "media_id": None, "url": None, "error": "No WP username"}
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/webp",
    }
    try:
        resp = requests.post(f"{base_url}/wp-json/wp/v2/media", headers=headers,
                             data=image_bytes, timeout=90)
        if resp.status_code in (200, 201):
            data = resp.json()
            media_id = data.get("id")
            source_url = data.get("source_url", "")
            log(f"  ✅ Uploaded {filename} → media_id={media_id}")
            return {"success": True, "media_id": media_id, "url": source_url, "error": None}
        err_text = resp.text[:300]
        log(f"  ❌ Upload failed {resp.status_code}: {err_text}")
        return {"success": False, "media_id": None, "url": None, "error": f"WP {resp.status_code}: {err_text}"}
    except Exception as e:
        log(f"  ❌ Upload exception: {e}")
        return {"success": False, "media_id": None, "url": None, "error": str(e)}


def publish_to_wordpress(title, content, wp_url, wp_password, status="publish",
                         meta_description="", featured_media_id=None, category_ids=None):
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    if not wp_user:
        return {"success": False, "error": "No WP username"}
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}
    payload = {"title": title, "content": content, "status": status}
    if featured_media_id:
        payload["featured_media"] = int(featured_media_id)
    if category_ids:
        payload["categories"] = category_ids
    if meta_description:
        payload["meta"] = {"_yoast_wpseo_metadesc": meta_description}
    try:
        resp = requests.post(f"{base_url}/wp-json/wp/v2/posts", headers=headers,
                             json=payload, timeout=60)
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"success": True, "post_id": data["id"],
                    "post_url": data.get("link", ""), "error": None}
        try:
            err = resp.json().get("message", resp.text[:300])
        except:
            err = resp.text[:300]
        return {"success": False, "error": f"WP {resp.status_code}: {err}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_wp_categories(wp_url, wp_password):
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    try:
        resp = requests.get(f"{base_url}/wp-json/wp/v2/categories?per_page=100",
                            headers={"Authorization": f"Basic {credentials}"}, timeout=15)
        if resp.status_code == 200:
            return [{"id": c["id"], "name": c["name"]} for c in resp.json()]
    except Exception:
        pass
    return []


def fetch_internal_links(wp_url, wp_password, max_posts=200):
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    links = []
    page = 1
    while len(links) < max_posts:
        try:
            resp = requests.get(
                f"{base_url}/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=id,title,link&status=publish",
                headers=headers, timeout=15)
            if resp.status_code != 200:
                break
            posts = resp.json()
            if not posts:
                break
            for p in posts:
                clean = re.sub(r"<[^>]+>", "", p["title"]["rendered"]).strip()
                links.append({"title": clean, "url": p["link"]})
            if len(posts) < 100:
                break
            page += 1
        except Exception:
            break
    return links


def inject_internal_links(html, links, current_title, max_links=4, main_color="#ea580c"):
    if not links or not html:
        return html
    injected = 0
    used_urls = set()
    current_lower = current_title.lower()
    for link in links:
        if injected >= max_links:
            break
        link_title = link.get("title", "").strip()
        link_url = link.get("url", "")
        if not link_title or not link_url or link_url in used_urls:
            continue
        if link_title.lower() == current_lower:
            continue
        words = link_title.split()
        if len(words) < 3:
            continue
        link_words = set(link_title.lower().split())
        current_words = set(current_lower.split())
        if len(link_words & current_words) / max(len(link_words), 1) > 0.5:
            continue
        pattern = re.compile(re.escape(link_title), re.IGNORECASE)
        if pattern.search(html):
            anchor = (f'<a href="{link_url}" style="color:{main_color};text-decoration:underline;'
                      f'font-weight:500;" title="{link_title}">{link_title}</a>')
            html = pattern.sub(anchor, html, count=1)
            used_urls.add(link_url)
            injected += 1
            continue
        if len(words) >= 4:
            short = " ".join(words[-3:])
            sp = re.compile(re.escape(short), re.IGNORECASE)
            if sp.search(html):
                anchor = (f'<a href="{link_url}" style="color:{main_color};text-decoration:underline;'
                          f'font-weight:500;" title="{link_title}">{short}</a>')
                html = sp.sub(anchor, html, count=1)
                used_urls.add(link_url)
                injected += 1
    return html


def inject_images_into_article(html, image_results, title):
    """Replace ##IMAGE1## ##IMAGE2## ##IMAGE3## with actual img tags."""
    placeholders = ["##IMAGE1##", "##IMAGE2##", "##IMAGE3##"]
    for i, ph in enumerate(placeholders):
        img_idx = i + 1  # index 0 = featured, 1/2/3 = body
        img_data = image_results[img_idx] if img_idx < len(image_results) else None
        if img_data and img_data.get("url"):
            img_tag = (
                f'<figure style="margin:28px auto;text-align:center;max-width:720px;">'
                f'<img src="{img_data["url"]}" alt="{title}" loading="lazy" '
                f'style="width:100%;border-radius:14px;box-shadow:0 4px 24px rgba(0,0,0,0.12);display:block;" />'
                f'</figure>'
            )
            html = html.replace(ph, img_tag)
        else:
            html = html.replace(ph, "")
    return html


# ─── Canva Pinterest Pin ──────────────────────────────────────────────────────

def _enforce_4_words(text):
    """Ensure hook is exactly 4 words. Trim or pad as needed."""
    words = text.strip().split()
    if len(words) >= 4:
        return " ".join(words[:4])
    # Pad with generic word if too short
    while len(words) < 4:
        words.append("Now")
    return " ".join(words[:4])


def generate_hook_title(api_key, title):
    """Generate an exactly-4-word hook title using AI."""
    try:
        prompt = HOOK_TITLE_PROMPT.replace("{title}", title)
        raw = ai_call(api_key, prompt, prefer_fast=True)
        data = parse_json_response(raw)
        hook = data.get("hook", "")
        if hook:
            return _enforce_4_words(hook)
    except Exception:
        pass
    # Fallback: take first 4 meaningful words from title
    words = [w for w in title.split() if len(w) > 2]
    if len(words) >= 4:
        return " ".join(words[:4])
    return _enforce_4_words(title)


def create_canva_pin_image(canva_template_url, article_images, hook_title, api_key,
                           title="", log_fn=None):
    """
    Create a Pinterest pin image by:
    1. Downloading the Canva template as a base image (via screenshot/export URL trick)
    2. Picking the best article image (first available body image)
    3. Compositing the article image into the template canvas
    4. Overlaying the 4-word hook title as bold text
    Returns: dict with keys 'image_bytes' (WebP bytes), 'hook_title', 'error'
    """
    def log(m):
        if log_fn: log_fn(m)

    # Ensure hook is exactly 4 words
    hook = _enforce_4_words(hook_title) if hook_title else generate_hook_title(api_key, title)
    log(f"  🎨 Hook title (4 words): {hook}")

    # Find best article body image (prefer index 1, fallback to 2, 3)
    article_img_bytes = None
    article_img_url = None
    for idx in [1, 2, 3]:
        if idx < len(article_images) and article_images[idx].get("url"):
            article_img_url = article_images[idx]["url"]
            log(f"  🖼️ Using article image {idx} for pin: {article_img_url[:60]}")
            break

    if article_img_url:
        try:
            r = requests.get(article_img_url, timeout=30)
            if r.status_code == 200:
                article_img_bytes = r.content
        except Exception as e:
            log(f"  ⚠️ Could not download article image: {e}")

    # Try to fetch Canva template as base
    # Canva share URLs can be accessed as images via their embed endpoint
    canva_base_bytes = None
    try:
        # Canva public design URLs: convert to export-friendly format
        # Pattern: https://www.canva.com/design/DESIGN_ID/... → use as background
        design_id_match = re.search(r"/design/([A-Za-z0-9_-]+)/", canva_template_url)
        if design_id_match:
            design_id = design_id_match.group(1)
            # Try Canva's OG image (thumbnail) as template base
            og_url = f"https://www.canva.com/design/{design_id}/view?utm_content={design_id}"
            # Fetch OG meta image from Canva page
            page_resp = requests.get(canva_template_url, timeout=20,
                                     headers={"User-Agent": "Mozilla/5.0"})
            if page_resp.status_code == 200:
                og_match = re.search(
                    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
                    page_resp.text)
                if not og_match:
                    og_match = re.search(
                        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                        page_resp.text)
                if og_match:
                    img_url = og_match.group(1)
                    log(f"  📐 Canva template thumbnail found")
                    img_resp = requests.get(img_url, timeout=30)
                    if img_resp.status_code == 200:
                        canva_base_bytes = img_resp.content
                        log("  ✅ Canva template base downloaded")
    except Exception as e:
        log(f"  ⚠️ Could not fetch Canva template: {e}")

    # Now composite: template base + article image + hook text
    try:
        # Pinterest optimal size: 1000x1500 (2:3 ratio)
        PIN_W, PIN_H = 1000, 1500

        # ── Build base canvas ──
        if canva_base_bytes:
            try:
                base_img = Image.open(io.BytesIO(canva_base_bytes)).convert("RGBA")
                base_img = base_img.resize((PIN_W, PIN_H), Image.LANCZOS)
                log("  ✅ Using Canva template as base")
            except Exception:
                base_img = None
        else:
            base_img = None

        # If no Canva base, create a styled gradient background
        if not base_img:
            log("  ℹ️ Creating styled background (Canva template unavailable)")
            base_img = Image.new("RGBA", (PIN_W, PIN_H), (255, 255, 255, 255))
            # Gradient effect using multiple rectangles
            draw_bg = ImageDraw.Draw(base_img)
            for y in range(PIN_H):
                ratio = y / PIN_H
                r = int(255 * (1 - ratio * 0.15))
                g = int(245 * (1 - ratio * 0.1))
                b = int(235 * (1 - ratio * 0.05))
                draw_bg.line([(0, y), (PIN_W, y)], fill=(r, g, b, 255))

        # ── Place article image in upper 60% ──
        if article_img_bytes:
            try:
                art_img = Image.open(io.BytesIO(article_img_bytes)).convert("RGBA")
                # Crop/resize to fill top portion (60% of pin height)
                img_area_h = int(PIN_H * 0.62)
                # Scale to fill width
                scale = PIN_W / art_img.width
                new_h = int(art_img.height * scale)
                art_img = art_img.resize((PIN_W, new_h), Image.LANCZOS)
                # Center crop to img_area_h
                if new_h > img_area_h:
                    top = (new_h - img_area_h) // 2
                    art_img = art_img.crop((0, top, PIN_W, top + img_area_h))
                else:
                    # Pad with white if too short
                    padded = Image.new("RGBA", (PIN_W, img_area_h), (255, 255, 255, 255))
                    padded.paste(art_img, (0, (img_area_h - new_h) // 2))
                    art_img = padded
                base_img.paste(art_img, (0, 0), art_img)
                log("  ✅ Article image composited onto pin")
            except Exception as e:
                log(f"  ⚠️ Could not composite article image: {e}")

        # ── Draw hook title text in bottom 38% ──
        draw = ImageDraw.Draw(base_img)
        text_area_top = int(PIN_H * 0.64)
        text_area_h = PIN_H - text_area_top

        # Background panel for text area
        panel = Image.new("RGBA", (PIN_W, text_area_h), (255, 255, 255, 240))
        base_img.paste(panel, (0, text_area_top), panel)

        # Accent bar at top of text area
        accent_color = (234, 88, 12, 255)  # orange default
        draw.rectangle([(0, text_area_top), (PIN_W, text_area_top + 8)], fill=accent_color)

        # Draw 4-word hook — each word on its own line for impact
        hook_words = hook.strip().split()[:4]
        # Try to load a bold font, fall back to default
        font_large = None
        font_small = None
        font_sizes_to_try = [120, 100, 80]
        for fsize in font_sizes_to_try:
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fsize)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
                break
            except Exception:
                pass
        if font_large is None:
            try:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            except Exception:
                font_large = None
                font_small = None

        if font_large:
            # Calculate line height and starting Y
            line_h = int(text_area_h / (len(hook_words) + 1.5))
            start_y = text_area_top + 40

            for i, word in enumerate(hook_words):
                y_pos = start_y + i * line_h
                # Shadow
                draw.text((PIN_W // 2 + 3, y_pos + 3), word.upper(),
                          font=font_large, fill=(0, 0, 0, 80), anchor="mt")
                # Main text
                draw.text((PIN_W // 2, y_pos), word.upper(),
                          font=font_large, fill=(30, 30, 30, 255), anchor="mt")

            # Small URL/brand hint at bottom
            if font_small:
                draw.text((PIN_W // 2, PIN_H - 40), "Save this pin! 📌",
                          font=font_small, fill=(150, 150, 150, 200), anchor="mt")
        else:
            # Fallback: simple text without custom font
            draw.text((50, text_area_top + 80), hook.upper(),
                      fill=(30, 30, 30, 255))

        # ── Convert to WebP bytes ──
        final_rgb = base_img.convert("RGB")
        buf = io.BytesIO()
        final_rgb.save(buf, format="WEBP", quality=85, method=1)
        pin_bytes = buf.getvalue()

        log(f"  ✅ Pin image created ({len(pin_bytes)//1024}KB)")
        return {"image_bytes": pin_bytes, "hook_title": hook, "error": None}

    except Exception as e:
        log(f"  ❌ Pin image creation failed: {e}")
        return {"image_bytes": None, "hook_title": hook, "error": str(e)}


# ─── Pinterest ────────────────────────────────────────────────────────────────

def generate_pin_content(api_key, title, article_url, pinterest_prompt=""):
    try:
        prompt = (pinterest_prompt.strip() if pinterest_prompt.strip() else DEFAULT_PINTEREST_PROMPT)\
            .replace("{title}", title).replace("{url}", article_url)
        raw = ai_call(api_key, prompt, prefer_fast=True)
        data = parse_json_response(raw)
        return {
            "success": True,
            "pin_title": data.get("pin_title", title[:60]),
            "pin_description": data.get("pin_description", ""),
            "alt_text": data.get("alt_text", title),
            "hashtags": data.get("hashtags", [])
        }
    except Exception as e:
        return {
            "success": False,
            "pin_title": title[:60],
            "pin_description": f"Check this out! {article_url}",
            "alt_text": title,
            "hashtags": [],
            "error": str(e)
        }


def get_pinterest_boards(access_token):
    try:
        resp = requests.get(
            "https://api.pinterest.com/v5/boards",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"page_size": 50}, timeout=15)
        if resp.status_code == 200:
            return [{"id": b["id"], "name": b["name"]} for b in resp.json().get("items", [])]
        return []
    except Exception:
        return []


def create_pinterest_pin(access_token, board_id, pin_title, pin_description,
                         alt_text, article_url, image_url=None, image_bytes=None,
                         wp_url="", wp_password="", log_fn=None):
    """
    Create a Pinterest pin.
    If image_bytes provided (Canva composite), upload it to WP first to get a public URL,
    then use that URL for the pin.
    Falls back to image_url if bytes not available.
    """
    def log(m):
        if log_fn: log_fn(m)

    final_image_url = image_url or ""

    # If we have composited pin image bytes, upload to WP to get a public URL
    if image_bytes and wp_url and wp_password:
        try:
            slug = re.sub(r"[^a-z0-9]+", "-", pin_title.lower()[:40]).strip("-")
            fname = f"pin-{slug}-{int(time.time())}.webp"
            up = upload_image_to_wordpress(wp_url, wp_password, image_bytes, fname, log)
            if up.get("success") and up.get("url"):
                final_image_url = up["url"]
                log(f"  ✅ Pin image uploaded to WP: {final_image_url[:60]}")
            else:
                log(f"  ⚠️ Pin image WP upload failed, falling back to article image")
        except Exception as e:
            log(f"  ⚠️ Pin image upload error: {e}")

    if not final_image_url:
        log("  ⚠️ No image URL for pin — skipping")
        return {"success": False, "pin_id": None, "error": "No image URL for pin"}

    try:
        resp = requests.post(
            "https://api.pinterest.com/v5/pins",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={
                "board_id": board_id,
                "title": pin_title[:100],
                "description": pin_description[:500],
                "alt_text": alt_text[:500],
                "link": article_url,
                "media_source": {"source_type": "image_url", "url": final_image_url}
            }, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "pin_id": resp.json().get("id", ""), "error": None,
                    "pin_image_url": final_image_url}
        return {"success": False, "pin_id": None,
                "error": resp.json().get("message", resp.text[:200])}
    except Exception as e:
        return {"success": False, "pin_id": None, "error": str(e)}


def run_pinterest_bot(api_key, access_token, articles, board_ids, pinterest_prompt="",
                      pin_delay_min=0, canva_template_url="", wp_url="", wp_password="",
                      log_fn=None):
    def log(m):
        if log_fn: log_fn(m)

    results = []
    for art in articles:
        title = art.get("title", "")
        url = art.get("post_url", "")
        featured_img = art.get("featured_image_url", "")
        article_images = art.get("image_results", [])

        log(f"📌 {title}")
        if not url:
            log("  ✗ No URL")
            results.append({"title": title, "status": "failed", "error": "No URL"})
            continue

        log("  ✦ Generating pin content...")
        pin_data = generate_pin_content(api_key, title, url, pinterest_prompt)
        log(f"  ✓ {pin_data['pin_title']}")

        # ── Build pin image ──
        pin_image_bytes = None
        hook_title = ""
        if canva_template_url and canva_template_url.strip():
            log("  🎨 Creating Canva-based pin image...")
            hook_title = generate_hook_title(api_key, title)
            pin_result = create_canva_pin_image(
                canva_template_url=canva_template_url,
                article_images=article_images,
                hook_title=hook_title,
                api_key=api_key,
                title=title,
                log_fn=log
            )
            if pin_result.get("image_bytes"):
                pin_image_bytes = pin_result["image_bytes"]
                hook_title = pin_result.get("hook_title", hook_title)
                log(f"  ✅ Pin image ready, hook: '{hook_title}'")
            else:
                log(f"  ⚠️ Pin image failed: {pin_result.get('error')} — using article image")

        if pin_delay_min > 0:
            log(f"  ⏱ Waiting {pin_delay_min}m...")
            time.sleep(pin_delay_min * 60)

        article_results = []
        for board_id in board_ids:
            log(f"  → Board {board_id}...")
            r = create_pinterest_pin(
                access_token=access_token,
                board_id=board_id,
                pin_title=pin_data["pin_title"],
                pin_description=pin_data["pin_description"],
                alt_text=pin_data["alt_text"],
                article_url=url,
                image_url=featured_img,          # fallback: featured image
                image_bytes=pin_image_bytes,      # preferred: Canva composite
                wp_url=wp_url,
                wp_password=wp_password,
                log_fn=log
            )
            log(f"  {'✅' if r['success'] else '❌'} {r.get('pin_id') or r.get('error')}")
            article_results.append({"board_id": board_id, **r})

        results.append({
            "title": title,
            "pin_title": pin_data["pin_title"],
            "pin_description": pin_data.get("pin_description", ""),
            "alt_text": pin_data.get("alt_text", ""),
            "hook_title": hook_title,
            "boards": article_results,
            "status": "sent" if any(r["success"] for r in article_results) else "failed"
        })
    return results


# ─── Full Pipeline ────────────────────────────────────────────────────────────

def run_full_pipeline(title, gemini_key, goapi_key="", wp_url="", wp_password="",
                      publish_status="publish", mj_template="", custom_prompt="",
                      card_prompt="", show_card=True, use_images=False,
                      use_pollinations=False, pollinations_prompt="",
                      internal_links=None, category_ids=None, max_links=4,
                      use_internal_links=True, log_fn=None):

    def log(msg):
        if log_fn: log_fn(msg)

    art_result = [None]
    card_result = [None]
    # IMPORTANT: 4 slots. index 0 = featured image, 1/2/3 = body images
    image_results = [{"url": None, "media_id": None} for _ in range(4)]

    # Track per-thread completion for proper sequencing
    art_done = threading.Event()
    images_done = threading.Event()

    _log_lock = threading.Lock()

    def safe_log(msg):
        with _log_lock:
            log(msg)

    # ── Thread: Generate Article ──
    def _gen_article():
        safe_log("✏️ Generating article...")
        result = generate_article(title, gemini_key, custom_prompt=custom_prompt)
        art_result[0] = result
        art_done.set()
        if result["success"]:
            wc = len(re.sub(r"<[^>]+>", "", result["content"]).split())
            safe_log(f"✅ Article ready (~{wc} words)")
        else:
            safe_log(f"❌ Article failed: {result['error']}")

    # ── Thread: Generate Card (waits for article colors) ──
    def _gen_card():
        if not show_card:
            return
        safe_log("🃏 Generating card...")
        # Wait for article to get brand colors (max 120s)
        art_done.wait(timeout=120)
        mc = "#ea580c"
        lb = "#fff7ed"
        bc = "#fdba74"
        if art_result[0] and art_result[0].get("parsed"):
            p = art_result[0]["parsed"]
            mc = p.get("MAIN", mc)
            lb = p.get("LIGHT_BG", lb)
            bc = p.get("BORDER", bc)
        card_html = generate_card(title, gemini_key, card_prompt=card_prompt,
                                  main_color=mc, light_bg=lb, border_color=bc)
        card_result[0] = card_html
        safe_log("✅ Card ready" if card_html else "⚠️ Card failed")

    # ── Thread: Generate Images ──
    def _gen_images():
        if not use_images:
            safe_log("⏭️ Images disabled (enable in Generate page)")
            images_done.set()
            return
        if not use_pollinations and not goapi_key:
            safe_log("⚠️ No image source configured")
            images_done.set()
            return

        names = ["featured", "body-1", "body-2", "body-3"]
        img_threads = []
        img_events = [threading.Event() for _ in range(4)]

        def _gen_single(idx):
            try:
                slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                fname = f"{slug}-{names[idx]}.webp"

                if use_pollinations:
                    tpl = pollinations_prompt or "Professional editorial photography of {title}, natural light, 4K"
                    ip = tpl.replace("{title}", title).replace("{recipe_name}", title)
                    safe_log(f"  🖼️ Image {idx + 1}/4 via Pollinations...")
                    res = generate_pollinations_image(ip)

                    if not res.get("url"):
                        safe_log(f"  ⚠️ Pollinations image {idx + 1} failed: {res.get('error', 'unknown')}")
                        return

                    raw = res.get("raw_bytes")
                    webp = bytes_to_webp(raw) if raw else download_and_convert_webp(res["url"])

                    if webp and wp_url and wp_password:
                        up = upload_image_to_wordpress(wp_url, wp_password, webp, fname, safe_log)
                        if up.get("success") and up.get("media_id"):
                            image_results[idx] = {"url": up["url"], "media_id": up["media_id"]}
                            safe_log(f"  ✅ Image {idx + 1} uploaded (media_id={up['media_id']})")
                            return
                        else:
                            safe_log(f"  ⚠️ WP upload failed for image {idx + 1}: {up.get('error')}")
                    # Fallback: direct URL
                    image_results[idx] = {"url": res["url"], "media_id": None}

                elif goapi_key:
                    tpl = mj_template or "Close up {recipe_name}, professional food photography, natural light --ar 2:3"
                    ip = tpl.replace("{recipe_name}", title).replace("{title}", title)
                    if "--ar" not in ip:
                        ip += " --ar 2:3"
                    safe_log(f"  🖼️ Image {idx + 1}/4 via Midjourney...")
                    res = generate_midjourney_image(goapi_key, ip, safe_log)

                    if not res.get("url"):
                        safe_log(f"  ⚠️ MJ image {idx + 1} failed: {res.get('error', 'unknown')}")
                        return

                    webp = download_and_convert_webp(res["url"])
                    if webp and wp_url and wp_password:
                        up = upload_image_to_wordpress(wp_url, wp_password, webp, fname, safe_log)
                        if up.get("success") and up.get("media_id"):
                            image_results[idx] = {"url": up["url"], "media_id": up["media_id"]}
                            safe_log(f"  ✅ Image {idx + 1} uploaded (media_id={up['media_id']})")
                            return
                        else:
                            safe_log(f"  ⚠️ WP upload failed: {up.get('error')}")
                    image_results[idx] = {"url": res["url"], "media_id": None}

            except Exception as ex:
                safe_log(f"  ❌ Image {idx + 1} error: {ex}")
            finally:
                img_events[idx].set()  # always signal done

        for idx in range(4):
            t = threading.Thread(target=_gen_single, args=(idx,), daemon=True)
            img_threads.append(t)
            t.start()

        # Wait for ALL image threads to finish
        for t in img_threads:
            t.join(timeout=300)

        # Signal images complete
        images_done.set()

        for idx in range(4):
            r = image_results[idx]
            if r.get("media_id"):
                safe_log(f"  📸 Image {idx + 1}: media_id={r['media_id']}, url={r.get('url', '')[:60]}")
            elif r.get("url"):
                safe_log(f"  📸 Image {idx + 1}: direct URL (no WP upload)")
            else:
                safe_log(f"  📸 Image {idx + 1}: not generated")

    # ── Launch article + card + images in parallel ──
    all_threads = []
    for fn in [_gen_article, _gen_card, _gen_images]:
        t = threading.Thread(target=fn, daemon=True)
        all_threads.append(t)
        t.start()

    # ── Wait for ARTICLE first (required to publish) ──
    art_done.wait(timeout=300)

    # ── Wait for FEATURED IMAGE specifically before publishing ──
    # We wait up to 5 minutes for the featured image (index 0) to be ready
    if use_images:
        log("⏳ Waiting for featured image upload before publishing...")
        featured_wait_start = time.time()
        while time.time() - featured_wait_start < 300:
            r0 = image_results[0]
            if r0.get("media_id") or r0.get("url"):
                # Featured image is ready (either uploaded or at least has URL)
                log("✅ Featured image ready — proceeding to publish")
                break
            # Also check if images thread is fully done
            if images_done.is_set():
                log("ℹ️ Images thread complete")
                break
            time.sleep(2)

    # ── Wait for card too ──
    card_timeout = time.time() + 60
    while card_result[0] is None and time.time() < card_timeout and show_card:
        time.sleep(1)

    # Check article result
    art = art_result[0]
    if not art or not art["success"]:
        # Signal done to avoid hanging
        images_done.set()
        return {"success": False, "error": art["error"] if art else "Article thread failed"}

    content = art["content"]

    # Inject body images
    content = inject_images_into_article(content, image_results, title)

    # Append card
    if show_card and card_result[0]:
        content += "\n" + card_result[0]
        log("✅ Card appended")

    # Inject internal links
    _links = internal_links
    if use_internal_links and not _links and wp_url and wp_password:
        log("🔗 Fetching internal links...")
        try:
            _links = fetch_internal_links(wp_url, wp_password, max_posts=200)
            log(f"🔗 Loaded {len(_links)} posts")
        except Exception as e:
            log(f"⚠️ Links error: {e}")
    if _links and use_internal_links:
        mc = art.get("parsed", {}).get("MAIN", "#ea580c")
        content = inject_internal_links(content, _links, title,
                                        max_links=max_links, main_color=mc)
        log("🔗 Internal links injected")

    # Publish
    meta = generate_meta_description(title)
    wp_title = art.get("seo_title") or title
    log("📤 Publishing to WordPress...")

    # ── Featured image: MUST have media_id (integer) for WP to set it ──
    featured_id = None
    featured_url = None
    r0 = image_results[0] if image_results else {}

    if r0.get("media_id"):
        try:
            featured_id = int(r0["media_id"])
            featured_url = r0.get("url", "")
            log(f"🖼️ Featured image: media_id={featured_id}")
        except (ValueError, TypeError) as e:
            log(f"⚠️ Invalid media_id: {r0['media_id']} ({e})")
    elif r0.get("url"):
        log(f"⚠️ Image URL exists but no media_id — featured image will NOT be set in WP sidebar.")
        log(f"   Check WP credentials have media upload permission.")
        featured_url = r0.get("url", "")
    else:
        if use_images:
            log("⚠️ No featured image generated")

    pub = publish_to_wordpress(
        title=wp_title, content=content,
        wp_url=wp_url, wp_password=wp_password,
        status=publish_status, meta_description=meta,
        featured_media_id=featured_id,
        category_ids=category_ids,
    )

    if pub["success"]:
        log(f"🎉 Published! → {pub.get('post_url', '')}")
        if featured_id:
            log(f"🖼️ Featured image set (media_id={featured_id})")
        pub["featured_image_url"] = featured_url
        pub["featured_media_id"] = featured_id
        # Store image_results for Pinterest bot to use later
        pub["image_results"] = image_results
    else:
        log(f"❌ Publish failed: {pub['error']}")

    # Wait for remaining threads to finish cleanly
    overall_deadline = time.time() + 30
    for t in all_threads:
        remaining = max(0, overall_deadline - time.time())
        t.join(timeout=remaining)

    return pub


# ─── Test helpers ─────────────────────────────────────────────────────────────

def test_gemini_key(api_key):
    try:
        keys = [k.strip() for k in api_key.split(",") if k.strip()]
        for key in keys:
            if key.startswith("gsk_"):
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": "llama-3.1-8b-instant",
                          "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5},
                    timeout=15)
                if resp.status_code == 200:
                    return {"success": True, "message": "✅ Groq key works! 🚀"}
                elif resp.status_code == 429:
                    return {"success": True, "message": "✅ Groq key valid (rate limited)"}
                return {"success": False, "message": f"❌ Groq error: {resp.status_code}"}
            elif key.startswith("AIza"):
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
                resp = requests.post(url, json={
                    "contents": [{"parts": [{"text": "Say OK"}]}],
                    "generationConfig": {"maxOutputTokens": 5}
                }, timeout=15)
                if resp.status_code == 200:
                    return {"success": True, "message": "✅ Gemini key works!"}
                return {"success": False, "message": f"❌ Gemini error: {resp.status_code}"}
        return {"success": False, "message": "❌ Use gsk_ (Groq) or AIza (Gemini)"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def test_goapi_key(api_key):
    try:
        resp = requests.get("https://api.goapi.ai/api/v1/task",
                            headers={"x-api-key": api_key}, timeout=10)
        ok = resp.status_code in (200, 405)
        return {"success": ok,
                "message": "✅ GoAPI key accepted!" if ok else "❌ Invalid GoAPI key"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def test_wordpress(wp_url, wp_password):
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    if not wp_user:
        return {"success": False, "message": "❌ Format: username:password"}
    try:
        credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
        resp = requests.get(f"{base_url}/wp-json/wp/v2/users/me",
                            headers={"Authorization": f"Basic {credentials}"}, timeout=10)
        if resp.status_code == 200:
            return {"success": True,
                    "message": f"✅ Connected as: {resp.json().get('name', wp_user)}"}
        return {"success": False,
                "message": f"❌ HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def test_pinterest(access_token):
    try:
        resp = requests.get("https://api.pinterest.com/v5/user_account",
                            headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
        if resp.status_code == 200:
            return {"success": True,
                    "message": f"✅ Pinterest: {resp.json().get('username', 'connected')}"}
        return {"success": False,
                "message": f"❌ Pinterest error: {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": str(e)}