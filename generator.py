# -*- coding: utf-8 -*-
"""NicheFlow AI — generator.py FINAL FIXED"""
import requests, json, base64, re, time, io, threading
from PIL import Image

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


def _groq_call(api_key, prompt, prefer_fast=False):
    models = ["llama-3.1-8b-instant","gemma2-9b-it"] if prefer_fast else ["llama-3.3-70b-versatile","meta-llama/llama-4-scout-17b-16e-instruct","llama-3.1-70b-versatile","llama-3.1-8b-instant"]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_err = None
    for model in models:
        try:
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers,
                json={"model":model,"messages":[{"role":"user","content":prompt}],"max_tokens":8000,"temperature":0.7}, timeout=90)
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                if text and len(text.strip()) > 50: return text
            elif resp.status_code == 429: last_err="rate_limited"; continue
            else: last_err=f"HTTP {resp.status_code}"; continue
        except Exception as e: last_err=str(e); continue
    raise Exception(f"All Groq models failed: {last_err}")


def _gemini_call(api_key, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    resp = requests.post(url, json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.7,"maxOutputTokens":8000}}, timeout=90)
    if resp.status_code == 200:
        candidates = resp.json().get("candidates", [])
        if not candidates: raise Exception("Gemini: no candidates")
        text = candidates[0].get("content",{}).get("parts",[{}])[0].get("text","")
        if text and len(text.strip()) > 50: return text
        raise Exception("Gemini empty text")
    elif resp.status_code == 429: raise Exception("Gemini quota exceeded")
    else:
        try: err = resp.json().get("error",{}).get("message",resp.text[:200])
        except: err = resp.text[:200]
        raise Exception(f"Gemini {resp.status_code}: {err}")


def ai_call(api_key, prompt, prefer_fast=False):
    keys = [k.strip() for k in api_key.split(",") if k.strip()]
    last_err = None
    for key in keys:
        try:
            if key.startswith("gsk_"): return _groq_call(key, prompt, prefer_fast)
            elif key.startswith("AIza"): return _gemini_call(key, prompt)
            else: last_err = f"Unknown key format: {key[:8]}"
        except Exception as e: last_err=str(e); continue
    raise Exception(f"All AI keys failed: {last_err}")


def parse_json_response(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*","",text); text = re.sub(r"\s*```$","",text); text = text.strip()
    start = text.find("{"); end = text.rfind("}")+1
    if start >= 0 and end > start: text = text[start:end]
    return json.loads(text)


def generate_article(title, api_key, custom_prompt="", show_card=True):
    try:
        prompt = (custom_prompt.strip() if custom_prompt.strip() else DEFAULT_ARTICLE_PROMPT).replace("{title}", title)
        raw = ai_call(api_key, prompt, prefer_fast=False)
        try: parsed = parse_json_response(raw)
        except: return {"success":True,"content":raw,"seo_title":title,"excerpt":"","parsed":{}}
        if parsed.get("error") == "REJECTED": return {"success":False,"error":"Topic rejected"}
        html = parsed.get("html_content","")
        if not html: return {"success":False,"error":"Empty html_content"}
        for key in ["MAIN","MAIN_DARK","LIGHT_BG","BORDER"]:
            val = parsed.get(key,"")
            if val: html = html.replace(key, val)
        return {"success":True,"content":html,"seo_title":parsed.get("seo_title",title),"excerpt":parsed.get("excerpt",""),"parsed":parsed}
    except Exception as e: return {"success":False,"error":str(e)}


def generate_card(title, api_key, card_prompt="", main_color="#ea580c", light_bg="#fff7ed", border_color="#fdba74"):
    """Generate summary card with a FULLY CLICKABLE CTA button (works in WordPress)."""
    try:
        prompt = (card_prompt.strip() if card_prompt.strip() else DEFAULT_CARD_PROMPT).replace("{title}", title)
        raw = ai_call(api_key, prompt, prefer_fast=True)
        data = parse_json_response(raw)
        card_title = data.get("card_title", title)
        summary = data.get("summary","")
        key_points = data.get("key_points",[])
        quick_facts = data.get("quick_facts",[])
        cta_text = data.get("cta_text","Save this! 📌")

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


def generate_midjourney_image(goapi_key, prompt, log_fn=None):
    """
    Generate a Midjourney image and immediately download the raw bytes
    before the CDN URL expires (~60s window). Returns url + raw_bytes.
    """
    def log(m):
        if log_fn: log_fn(m)
    headers = {"x-api-key": goapi_key, "Content-Type": "application/json"}
    try:
        resp = requests.post("https://api.goapi.ai/api/v1/task", headers=headers,
            json={"model":"midjourney","task_type":"imagine","input":{"prompt":prompt,"process_mode":"fast"}}, timeout=30)
        if resp.status_code != 200: return {"url":None,"raw_bytes":None,"error":f"MJ error {resp.status_code}"}
        task_id = resp.json().get("data",{}).get("task_id")
        if not task_id: return {"url":None,"raw_bytes":None,"error":"No task_id"}
        log(f"  🎨 MJ task: {task_id}"); time.sleep(10)
        for attempt in range(90):
            time.sleep(3)
            poll = requests.get(f"https://api.goapi.ai/api/v1/task/{task_id}", headers=headers, timeout=15)
            if poll.status_code != 200: continue
            data = poll.json().get("data",{})
            status = data.get("status","")
            if status == "completed":
                url = data.get("output",{}).get("image_urls",[None])[0]
                if not url:
                    return {"url":None,"raw_bytes":None,"error":"No image URL"}
                log("  ✅ MJ ready — downloading immediately...")
                # ── FIX: download raw bytes RIGHT NOW before CDN URL expires ──
                try:
                    dl = requests.get(url, timeout=60, stream=True)
                    if dl.status_code == 200:
                        raw_bytes = dl.content
                        log(f"  ✅ Downloaded {len(raw_bytes)//1024}KB")
                        return {"url":url,"raw_bytes":raw_bytes,"error":None}
                    else:
                        log(f"  ⚠️ Download failed {dl.status_code}, returning URL only")
                        return {"url":url,"raw_bytes":None,"error":None}
                except Exception as dl_err:
                    log(f"  ⚠️ Download error: {dl_err}, returning URL only")
                    return {"url":url,"raw_bytes":None,"error":None}
            elif status == "failed":
                err = data.get("error",{}).get("message","Unknown")
                if "fast" in err.lower() or "quota" in err.lower():
                    log("  ⚠️ Fast quota, trying relax...")
                    resp2 = requests.post("https://api.goapi.ai/api/v1/task", headers=headers,
                        json={"model":"midjourney","task_type":"imagine","input":{"prompt":prompt,"process_mode":"relax"}}, timeout=30)
                    if resp2.status_code == 200: task_id = resp2.json().get("data",{}).get("task_id",task_id)
                    continue
                return {"url":None,"raw_bytes":None,"error":err}
            elif attempt % 5 == 0: log(f"  ⏳ Generating... ({attempt*3}s)")
        return {"url":None,"raw_bytes":None,"error":"Timeout 270s"}
    except Exception as e: return {"url":None,"raw_bytes":None,"error":str(e)}


def generate_pollinations_image(prompt, width=1024, height=1024):
    try:
        safe_prompt = requests.utils.quote(prompt[:400])
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={width}&height={height}&nologo=true&seed={int(time.time())}"
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200 and resp.headers.get("content-type","").startswith("image"):
            return {"url":url,"raw_bytes":resp.content,"error":None}
        return {"url":None,"raw_bytes":None,"error":f"Pollinations {resp.status_code}"}
    except Exception as e: return {"url":None,"raw_bytes":None,"error":str(e)}


def download_and_convert_webp(image_url, max_width=1920):
    """Download image from URL, convert to WebP, return bytes."""
    try:
        resp = requests.get(image_url, timeout=60, stream=True)
        if resp.status_code != 200: return None
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=80, method=1)
        return buf.getvalue()
    except Exception: return None


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
    except Exception: return None


def parse_wp_credentials(wp_url, wp_password):
    base_url = wp_url.rstrip("/")
    if ":" in wp_password:
        idx = wp_password.index(":")
        wp_user = wp_password[:idx].strip()
        wp_pass = wp_password[idx+1:].strip()
    else:
        wp_user = ""; wp_pass = wp_password.strip()
    return base_url, wp_user, wp_pass


def upload_image_to_wordpress(wp_url, wp_password, image_bytes, filename, log_fn=None):
    """Upload WebP bytes to WP media library. Returns dict with media_id and url."""
    def log(m):
        if log_fn: log_fn(m)
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    if not wp_user:
        log("  ⚠️ No WP username in credentials")
        return {"success":False,"media_id":None,"url":None,"error":"No WP username"}
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/webp",
    }
    try:
        resp = requests.post(f"{base_url}/wp-json/wp/v2/media", headers=headers, data=image_bytes, timeout=90)
        if resp.status_code in (200, 201):
            data = resp.json()
            media_id = data.get("id")
            source_url = data.get("source_url","")
            log(f"  ✅ Uploaded {filename} → media_id={media_id}")
            return {"success":True,"media_id":media_id,"url":source_url,"error":None}
        err_text = resp.text[:300]
        log(f"  ❌ Upload failed {resp.status_code}: {err_text}")
        return {"success":False,"media_id":None,"url":None,"error":f"WP {resp.status_code}: {err_text}"}
    except Exception as e:
        log(f"  ❌ Upload exception: {e}")
        return {"success":False,"media_id":None,"url":None,"error":str(e)}


def publish_to_wordpress(title, content, wp_url, wp_password, status="publish",
    meta_description="", featured_media_id=None, category_ids=None):
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    if not wp_user: return {"success":False,"error":"No WP username"}
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {"Authorization":f"Basic {credentials}","Content-Type":"application/json"}
    payload = {"title":title,"content":content,"status":status}
    if featured_media_id:
        payload["featured_media"] = int(featured_media_id)
    if category_ids: payload["categories"] = category_ids
    if meta_description: payload["meta"] = {"_yoast_wpseo_metadesc":meta_description}
    try:
        resp = requests.post(f"{base_url}/wp-json/wp/v2/posts", headers=headers, json=payload, timeout=60)
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"success":True,"post_id":data["id"],"post_url":data.get("link",""),"error":None}
        try: err = resp.json().get("message",resp.text[:300])
        except: err = resp.text[:300]
        return {"success":False,"error":f"WP {resp.status_code}: {err}"}
    except Exception as e: return {"success":False,"error":str(e)}


def fetch_wp_categories(wp_url, wp_password):
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    try:
        resp = requests.get(f"{base_url}/wp-json/wp/v2/categories?per_page=100",
            headers={"Authorization":f"Basic {credentials}"}, timeout=15)
        if resp.status_code == 200:
            return [{"id":c["id"],"name":c["name"]} for c in resp.json()]
    except Exception: pass
    return []


def fetch_internal_links(wp_url, wp_password, max_posts=200):
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {"Authorization":f"Basic {credentials}"}
    links = []; page = 1
    while len(links) < max_posts:
        try:
            resp = requests.get(f"{base_url}/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=id,title,link&status=publish",
                headers=headers, timeout=15)
            if resp.status_code != 200: break
            posts = resp.json()
            if not posts: break
            for p in posts:
                clean = re.sub(r"<[^>]+>","",p["title"]["rendered"]).strip()
                links.append({"title":clean,"url":p["link"]})
            if len(posts) < 100: break
            page += 1
        except Exception: break
    return links


def inject_internal_links(html, links, current_title, max_links=4, main_color="#ea580c"):
    if not links or not html: return html
    injected = 0; used_urls = set()
    current_lower = current_title.lower()
    for link in links:
        if injected >= max_links: break
        link_title = link.get("title","").strip()
        link_url = link.get("url","")
        if not link_title or not link_url or link_url in used_urls: continue
        if link_title.lower() == current_lower: continue
        words = link_title.split()
        if len(words) < 3: continue
        link_words = set(link_title.lower().split())
        current_words = set(current_lower.split())
        if len(link_words & current_words) / max(len(link_words), 1) > 0.5: continue
        pattern = re.compile(re.escape(link_title), re.IGNORECASE)
        if pattern.search(html):
            anchor = f'<a href="{link_url}" style="color:{main_color};text-decoration:underline;font-weight:500;" title="{link_title}">{link_title}</a>'
            html = pattern.sub(anchor, html, count=1)
            used_urls.add(link_url); injected += 1; continue
        if len(words) >= 4:
            short = " ".join(words[-3:])
            sp = re.compile(re.escape(short), re.IGNORECASE)
            if sp.search(html):
                anchor = f'<a href="{link_url}" style="color:{main_color};text-decoration:underline;font-weight:500;" title="{link_title}">{short}</a>'
                html = sp.sub(anchor, html, count=1)
                used_urls.add(link_url); injected += 1
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


def generate_pin_content(api_key, title, article_url, pinterest_prompt=""):
    try:
        prompt = (pinterest_prompt.strip() if pinterest_prompt.strip() else DEFAULT_PINTEREST_PROMPT).replace("{title}",title).replace("{url}",article_url)
        raw = ai_call(api_key, prompt, prefer_fast=True)
        data = parse_json_response(raw)
        return {"success":True,"pin_title":data.get("pin_title",title[:60]),"pin_description":data.get("pin_description",""),"alt_text":data.get("alt_text",title),"hashtags":data.get("hashtags",[])}
    except Exception as e:
        return {"success":False,"pin_title":title[:60],"pin_description":f"Check this out! {article_url}","alt_text":title,"hashtags":[],"error":str(e)}


def get_pinterest_boards(access_token):
    try:
        resp = requests.get("https://api.pinterest.com/v5/boards", headers={"Authorization":f"Bearer {access_token}"}, params={"page_size":50}, timeout=15)
        if resp.status_code == 200:
            return [{"id":b["id"],"name":b["name"]} for b in resp.json().get("items",[])]
        return []
    except Exception: return []


def create_pinterest_pin(access_token, board_id, pin_title, pin_description, alt_text, article_url, image_url):
    try:
        resp = requests.post("https://api.pinterest.com/v5/pins",
            headers={"Authorization":f"Bearer {access_token}","Content-Type":"application/json"},
            json={"board_id":board_id,"title":pin_title[:100],"description":pin_description[:500],"alt_text":alt_text[:500],"link":article_url,"media_source":{"source_type":"image_url","url":image_url}},
            timeout=30)
        if resp.status_code in (200,201): return {"success":True,"pin_id":resp.json().get("id",""),"error":None}
        return {"success":False,"pin_id":None,"error":resp.json().get("message",resp.text[:200])}
    except Exception as e: return {"success":False,"pin_id":None,"error":str(e)}


def run_pinterest_bot(api_key, access_token, articles, board_ids, pinterest_prompt="", pin_delay_min=0, log_fn=None):
    def log(m):
        if log_fn: log_fn(m)
    results = []
    for art in articles:
        title = art.get("title",""); url = art.get("post_url",""); featured_img = art.get("featured_image_url","")
        log(f"📌 {title}")
        if not url: log("  ✗ No URL"); results.append({"title":title,"status":"failed","error":"No URL"}); continue
        log("  ✦ Generating pin..."); pin_data = generate_pin_content(api_key, title, url, pinterest_prompt)
        log(f"  ✓ {pin_data['pin_title']}")
        if pin_delay_min > 0: log(f"  ⏱ Waiting {pin_delay_min}m..."); time.sleep(pin_delay_min*60)
        article_results = []
        for board_id in board_ids:
            log(f"  → Board {board_id}...")
            r = create_pinterest_pin(access_token, board_id, pin_data["pin_title"], pin_data["pin_description"], pin_data["alt_text"], url, featured_img or "")
            log(f"  {'✅' if r['success'] else '❌'} {r.get('pin_id') or r.get('error')}")
            article_results.append({"board_id":board_id,**r})
        results.append({"title":title,"pin_title":pin_data["pin_title"],"pin_description":pin_data.get("pin_description",""),"alt_text":pin_data.get("alt_text",""),"boards":article_results,"status":"sent" if any(r["success"] for r in article_results) else "failed"})
    return results


def run_full_pipeline(title, gemini_key, goapi_key="", wp_url="", wp_password="", publish_status="publish",
    mj_template="", custom_prompt="", card_prompt="", show_card=True, use_images=False,
    use_pollinations=False, pollinations_prompt="", internal_links=None, category_ids=None,
    max_links=4, use_internal_links=True, log_fn=None):

    def log(msg):
        if log_fn: log_fn(msg)

    art_result = [None]; card_result = [None]
    image_results = [{"url":None,"media_id":None} for _ in range(4)]
    all_threads = []; _log_lock = threading.Lock()

    def safe_log(msg):
        with _log_lock: log(msg)

    def _gen_article():
        safe_log("✏️ Generating article...")
        result = generate_article(title, gemini_key, custom_prompt=custom_prompt)
        art_result[0] = result
        if result["success"]:
            wc = len(re.sub(r"<[^>]+>","",result["content"]).split())
            safe_log(f"✅ Article ready (~{wc} words)")
        else:
            safe_log(f"❌ Article failed: {result['error']}")

    def _gen_card():
        if not show_card: return
        safe_log("🃏 Generating card...")
        deadline = time.time() + 120
        while art_result[0] is None and time.time() < deadline: time.sleep(1)
        mc="#ea580c"; lb="#fff7ed"; bc="#fdba74"
        if art_result[0] and art_result[0].get("parsed"):
            p=art_result[0]["parsed"]; mc=p.get("MAIN",mc); lb=p.get("LIGHT_BG",lb); bc=p.get("BORDER",bc)
        card_html = generate_card(title, gemini_key, card_prompt=card_prompt, main_color=mc, light_bg=lb, border_color=bc)
        card_result[0] = card_html
        safe_log("✅ Card ready" if card_html else "⚠️ Card failed")

    def _gen_images():
        if not use_images:
            safe_log("⏭️ Images disabled (enable in Generate page)")
            return
        if not use_pollinations and not goapi_key:
            safe_log("⚠️ No image source configured (need GoAPI key or enable Pollinations in Settings → Images)")
            return

        names = ["featured","body-1","body-2","body-3"]
        img_threads = []

        def _gen_single(idx):
            slug = re.sub(r"[^a-z0-9]+","-",title.lower()).strip("-")
            fname = f"{slug}-{names[idx]}.webp"

            if use_pollinations:
                tpl = pollinations_prompt or "Professional editorial photography of {title}, natural light, 4K"
                ip = tpl.replace("{title}",title).replace("{recipe_name}",title)
                safe_log(f"  🖼️ Image {idx+1}/4 via Pollinations...")
                res = generate_pollinations_image(ip)

                if not res.get("url") and not res.get("raw_bytes"):
                    safe_log(f"  ⚠️ Pollinations image {idx+1} failed: {res.get('error','unknown')}")
                    return

                # Use raw_bytes directly — already downloaded inside generate_pollinations_image
                raw = res.get("raw_bytes")
                webp = bytes_to_webp(raw) if raw else None

                if not webp:
                    safe_log(f"  ⚠️ WebP conversion failed for image {idx+1}")
                    # Still store the direct URL as fallback so body images show
                    if res.get("url"):
                        image_results[idx] = {"url": res["url"], "media_id": None}
                    return

                if wp_url and wp_password:
                    up = upload_image_to_wordpress(wp_url, wp_password, webp, fname, safe_log)
                    if up.get("success") and up.get("media_id"):
                        image_results[idx] = {"url": up["url"], "media_id": up["media_id"]}
                        safe_log(f"  ✅ Image {idx+1} uploaded to WP (media_id={up['media_id']})")
                        return
                    else:
                        safe_log(f"  ⚠️ WP upload failed for image {idx+1}: {up.get('error')}")

                # Fallback: use direct URL without WP upload
                image_results[idx] = {"url": res["url"], "media_id": None}

            elif goapi_key:
                tpl = mj_template or "Close up {recipe_name}, professional food photography, natural light --ar 2:3"
                arm = re.search(r"--ar\s+(\d+:\d+)", tpl)
                ar = arm.group(1) if arm else "2:3"
                ip = tpl.replace("{recipe_name}",title).replace("{title}",title)
                if "--ar" not in ip: ip += f" --ar {ar}"
                safe_log(f"  🖼️ Image {idx+1}/4 via Midjourney...")
                res = generate_midjourney_image(goapi_key, ip, safe_log)

                if not res.get("url") and not res.get("raw_bytes"):
                    safe_log(f"  ⚠️ MJ image {idx+1} failed: {res.get('error','unknown')}")
                    return

                # ── FIX: use raw_bytes captured immediately after MJ completed ──
                # This avoids the CDN URL expiry race condition entirely.
                raw = res.get("raw_bytes")
                if raw:
                    webp = bytes_to_webp(raw)
                else:
                    # raw_bytes missing — try downloading from URL as last resort
                    safe_log(f"  ⚠️ No raw bytes for image {idx+1}, trying URL download...")
                    webp = download_and_convert_webp(res["url"]) if res.get("url") else None

                if not webp:
                    safe_log(f"  ⚠️ WebP conversion failed for image {idx+1}")
                    # Still store the direct URL as fallback so body images show in article
                    if res.get("url"):
                        image_results[idx] = {"url": res["url"], "media_id": None}
                    return

                if wp_url and wp_password:
                    up = upload_image_to_wordpress(wp_url, wp_password, webp, fname, safe_log)
                    if up.get("success") and up.get("media_id"):
                        image_results[idx] = {"url": up["url"], "media_id": up["media_id"]}
                        safe_log(f"  ✅ Image {idx+1} uploaded (media_id={up['media_id']})")
                        return
                    else:
                        safe_log(f"  ⚠️ WP upload failed for image {idx+1}: {up.get('error')}")

                # Fallback to original MJ URL
                image_results[idx] = {"url": res["url"], "media_id": None}

        for idx in range(4):
            t = threading.Thread(target=_gen_single, args=(idx,), daemon=True)
            img_threads.append(t); t.start()
        for t in img_threads: t.join(timeout=300)

        # Log final image state
        for idx in range(4):
            r = image_results[idx]
            if r.get("media_id"):
                safe_log(f"  📸 Image {idx+1}: media_id={r['media_id']}, url={r.get('url','')[:60]}")
            elif r.get("url"):
                safe_log(f"  📸 Image {idx+1}: direct URL (no WP upload)")
            else:
                safe_log(f"  📸 Image {idx+1}: not generated")

    # Launch all threads in parallel
    for fn in [_gen_article, _gen_card, _gen_images]:
        t = threading.Thread(target=fn, daemon=True)
        all_threads.append(t); t.start()

    deadline = time.time() + 600
    while any(t.is_alive() for t in all_threads):
        if time.time() > deadline: log("⚠️ Timeout 10min"); break
        time.sleep(2)
    for t in all_threads: t.join(timeout=5)

    # Check article
    art = art_result[0]
    if not art or not art["success"]:
        return {"success":False,"error":art["error"] if art else "Article thread failed"}

    content = art["content"]

    # Inject body images (##IMAGE1## ##IMAGE2## ##IMAGE3##)
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
        except Exception as e: log(f"⚠️ Links error: {e}")
    if _links and use_internal_links:
        mc = art.get("parsed",{}).get("MAIN","#ea580c")
        content = inject_internal_links(content, _links, title, max_links=max_links, main_color=mc)
        log("🔗 Internal links injected")

    # Publish
    meta = generate_meta_description(title)
    wp_title = art.get("seo_title") or title
    log("📤 Publishing to WordPress...")

    # Get featured image media_id (index 0 = featured image)
    featured_id = None
    if image_results[0].get("media_id"):
        featured_id = image_results[0]["media_id"]
        log(f"🖼️ Setting featured image: media_id={featured_id}")
    else:
        log("⚠️ No featured image media_id — featured image will not be set")

    pub = publish_to_wordpress(
        title=wp_title, content=content,
        wp_url=wp_url, wp_password=wp_password,
        status=publish_status, meta_description=meta,
        featured_media_id=featured_id,
        category_ids=category_ids,
    )

    if pub["success"]:
        log(f"🎉 Published! → {pub.get('post_url','')}")
        pub["featured_image_url"] = image_results[0].get("url") if image_results[0] else None
        pub["featured_media_id"] = featured_id
    else:
        log(f"❌ Publish failed: {pub['error']}")

    return pub


def test_gemini_key(api_key):
    try:
        keys = [k.strip() for k in api_key.split(",") if k.strip()]
        for key in keys:
            if key.startswith("gsk_"):
                resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
                    json={"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"Say OK"}],"max_tokens":5}, timeout=15)
                if resp.status_code==200: return {"success":True,"message":"✅ Groq key works! 🚀"}
                elif resp.status_code==429: return {"success":True,"message":"✅ Groq key valid (rate limited)"}
                return {"success":False,"message":f"❌ Groq error: {resp.status_code}"}
            elif key.startswith("AIza"):
                url=f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
                resp=requests.post(url,json={"contents":[{"parts":[{"text":"Say OK"}]}],"generationConfig":{"maxOutputTokens":5}},timeout=15)
                if resp.status_code==200: return {"success":True,"message":"✅ Gemini key works!"}
                return {"success":False,"message":f"❌ Gemini error: {resp.status_code}"}
        return {"success":False,"message":"❌ Use gsk_ (Groq) or AIza (Gemini)"}
    except Exception as e: return {"success":False,"message":str(e)}


def test_goapi_key(api_key):
    try:
        resp=requests.get("https://api.goapi.ai/api/v1/task",headers={"x-api-key":api_key},timeout=10)
        ok=resp.status_code in (200,405)
        return {"success":ok,"message":"✅ GoAPI key accepted!" if ok else "❌ Invalid GoAPI key"}
    except Exception as e: return {"success":False,"message":str(e)}


def test_wordpress(wp_url, wp_password):
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    if not wp_user: return {"success":False,"message":"❌ Format: username:password"}
    try:
        credentials=base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
        resp=requests.get(f"{base_url}/wp-json/wp/v2/users/me",headers={"Authorization":f"Basic {credentials}"},timeout=10)
        if resp.status_code==200: return {"success":True,"message":f"✅ Connected as: {resp.json().get('name',wp_user)}"}
        return {"success":False,"message":f"❌ HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e: return {"success":False,"message":str(e)}


def test_pinterest(access_token):
    try:
        resp=requests.get("https://api.pinterest.com/v5/user_account",headers={"Authorization":f"Bearer {access_token}"},timeout=10)
        if resp.status_code==200: return {"success":True,"message":f"✅ Pinterest: {resp.json().get('username','connected')}"}
        return {"success":False,"message":f"❌ Pinterest error: {resp.status_code}"}
    except Exception as e: return {"success":False,"message":str(e)}