# -*- coding: utf-8 -*-
"""
NicheFlow AI — generator.py
Multi-user public SaaS. No hardcoded persona, no default niche.
All prompts, credentials, and settings come from the user.
"""

import requests
import json
import base64
import re
import time
import io
import threading
from PIL import Image


# ─────────────────────────────────────────
#  GROQ API
# ─────────────────────────────────────────

def _groq_call(api_key: str, prompt: str, prefer_fast: bool = False) -> str:
    if prefer_fast:
        model_order = ["llama-3.1-8b-instant", "gemma2-9b-it", "llama3-8b-8192"]
    else:
        model_order = [
            "llama-3.3-70b-versatile",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "llama3-70b-8192",
            "llama-3.1-8b-instant",
        ]
    last_error = ""
    for model in model_order:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "stream": False
                },
                timeout=90
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                if text and len(text.strip()) > 50:
                    return text
                last_error = f"{model}: empty response"
            elif resp.status_code == 429:
                last_error = f"{model}: rate limited"
                continue
            else:
                last_error = f"{model} error {resp.status_code}"
        except requests.exceptions.Timeout:
            last_error = f"{model}: timeout"
        except Exception as e:
            last_error = str(e)
    raise Exception(f"Groq: all models tried — {last_error}")


def _call_ai(api_key: str, prompt: str, prefer_fast: bool = False) -> str:
    key = api_key.strip()
    if key.startswith("gsk_"):
        return _groq_call(key, prompt, prefer_fast=prefer_fast)
    raise Exception("Unrecognized API key format. Use a Groq key (starts with gsk_) from console.groq.com")


# ─────────────────────────────────────────
#  PROMPT BUILDERS — zero defaults, user controls everything
# ─────────────────────────────────────────

def _build_article_prompt(title: str, user_article_prompt: str, user_html_structure: str,
                           user_design: dict, show_card: bool, use_internal_links: bool) -> str:
    design_hint = ""
    if user_design:
        main_color   = user_design.get("main_color", "#333333")
        accent_color = user_design.get("accent_color", "#ea580c")
        font_family  = user_design.get("font_family", "inherit")
        design_hint = (
            f"\nDesign variables to use in inline styles:\n"
            f"- Main color (headings, accents): {main_color}\n"
            f"- Accent / highlight color: {accent_color}\n"
            f"- Font family: {font_family}\n"
            f"Use these in all colored boxes, border-left sections, and headings.\n"
        )

    card_hint = "\nPlace the placeholder text ##RECIPE_CARD## at the end of the article body where the info card should appear.\n" if show_card else ""
    image_hints = "\nPlace ##IMAGE1## after the intro paragraphs, ##IMAGE2## after the middle section, ##IMAGE3## near the end.\n"

    structure_hint = ""
    if user_html_structure and user_html_structure.strip():
        structure_hint = f"\nUse this HTML structure/style template as your formatting guide:\n{user_html_structure.strip()}\n"

    return (
        f"You are an expert content writer. Return ONLY valid HTML — no markdown, no preamble, no JSON wrapper.\n\n"
        f"Write a complete, well-structured, SEO-optimized article for the topic: \"{title}\"\n\n"
        f"Follow these instructions from the publisher:\n{user_article_prompt.strip()}\n"
        f"{structure_hint}"
        f"{design_hint}"
        f"{card_hint}"
        f"{image_hints}\n"
        f"Rules:\n"
        f"- Output ONLY the HTML article body (no <html>, <head>, <body> tags)\n"
        f"- Use inline CSS styles for all formatting\n"
        f"- Do NOT include a card block yourself — use ##RECIPE_CARD## placeholder only\n"
        f"- Do NOT include broken image tags — images will be injected via ##IMAGE1## ##IMAGE2## ##IMAGE3##\n"
        f"- {'Include contextually relevant anchor text in <a href=\"INTERNAL_LINK_PLACEHOLDER\"> tags' if use_internal_links else 'Do NOT add any <a href> links'}\n"
        f"- Make the article genuinely useful, engaging, and unique\n"
    )


def _build_card_prompt(title: str, user_card_prompt: str, user_design: dict) -> str:
    main_color   = (user_design or {}).get("main_color", "#333333")
    accent_color = (user_design or {}).get("accent_color", "#ea580c")
    return (
        f"You are a structured data extractor. Return ONLY a valid JSON object — no markdown, no preamble.\n\n"
        f"For the topic \"{title}\", extract or generate structured card data following these instructions:\n"
        f"{user_card_prompt.strip()}\n\n"
        f"Always include at minimum:\n"
        f"{{\"card_title\": \"\", \"fields\": [{{\"label\": \"\", \"value\": \"\"}}], "
        f"\"main_color\": \"{main_color}\", \"accent_color\": \"{accent_color}\"}}\n\n"
        f"For recipe/food content also include: prep, cook, total, serves, calories, ingredients (array), instructions (array)\n"
        f"For travel content: best_time, budget, language, currency, top_attractions (array)\n"
        f"Adapt fields to what makes sense for the niche described in the publisher's instructions.\n\n"
        f"Topic: {title}"
    )


def _build_pinterest_prompt(title: str, article_url: str, user_pinterest_prompt: str) -> str:
    return (
        f"You are a Pinterest SEO expert. Return ONLY a valid JSON object — no markdown, no preamble.\n\n"
        f"Generate optimized Pinterest pin data for this article:\n"
        f"Title: {title}\nArticle URL: {article_url}\n\n"
        f"Publisher instructions:\n{user_pinterest_prompt.strip()}\n\n"
        f"Return ONLY this JSON:\n"
        f"{{\"pin_title\": \"\", \"pin_description\": \"\", \"alt_text\": \"\", \"keywords\": []}}\n\n"
        f"Rules:\n"
        f"- pin_title: max 100 chars, compelling, keyword-rich\n"
        f"- pin_description: max 500 chars, conversational, includes a call to action, ends with the article URL\n"
        f"- alt_text: max 100 chars, descriptive of what the featured image shows\n"
        f"- keywords: array of 5-10 relevant Pinterest search keywords"
    )


# ─────────────────────────────────────────
#  CLEAN HTML OUTPUT
# ─────────────────────────────────────────

def _clean_html(html: str) -> str:
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'\1', html)
    html = re.sub(r'```[\w]*\n?', '', html)
    html = html.replace('```', '')
    html = re.sub(r'<h2([^>]*)>', r'<h2\1 style="margin-top:2em;">', html)
    html = re.sub(r'\n{3,}', '\n\n', html)

    def _is_valid_img(tag):
        src = re.search(r'src=[\'\"](.*?)[\'\"]', tag)
        return src and src.group(1).startswith('https://')

    html = re.sub(
        r'<div[^>]*>\s*<img[^>]*/?\s*>\s*</div>',
        lambda m: m.group(0) if _is_valid_img(m.group(0)) else "",
        html, flags=re.DOTALL | re.IGNORECASE
    )
    html = re.sub(
        r'<img[^>]*/?>',
        lambda m: m.group(0) if _is_valid_img(m.group(0)) else "",
        html, flags=re.IGNORECASE
    )
    html = re.sub(r'alt="[^"]{0,3}"', 'alt=""', html)
    return html.strip()


# ─────────────────────────────────────────
#  CARD BUILDER — generic, niche-agnostic
# ─────────────────────────────────────────

def _build_card_html(card_data: dict, clickable: bool = False, article_url: str = "") -> str:
    M  = card_data.get("main_color",   "#333333")
    AC = card_data.get("accent_color", "#ea580c")
    title = card_data.get("card_title", "")

    stat_keys = ["prep", "cook", "total", "serves", "calories", "duration", "difficulty", "budget", "rating"]
    stat_icons = {"prep": "⏱️", "cook": "🔥", "total": "⏰", "serves": "👤",
                  "calories": "🔥", "duration": "⏱️", "difficulty": "⭐", "budget": "💰", "rating": "⭐"}
    stat_fields = [(stat_icons.get(k, "•"), k.upper(), card_data[k]) for k in stat_keys if card_data.get(k)]

    stats_html = ""
    if stat_fields:
        n = min(len(stat_fields), 4)
        stats_html = f'<div style="display:grid;grid-template-columns:repeat({n},1fr);background:#f9f9f9;border-bottom:2px solid {AC}20;">'
        for ico, lbl, val in stat_fields[:4]:
            stats_html += (
                f'<div style="padding:14px 8px;text-align:center;border-right:1px solid {AC}20;">'
                f'<div style="font-size:18px;margin-bottom:2px;">{ico}</div>'
                f'<div style="font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#999;">{lbl}</div>'
                f'<div style="font-size:14px;font-weight:800;color:{M};">{val}</div>'
                f'</div>'
            )
        stats_html += '</div>'

    generic_fields = card_data.get("fields", [])
    fields_html = ""
    if generic_fields:
        fields_html = f'<div style="padding:20px 24px;border-bottom:1px solid {AC}20;">'
        for f in generic_fields:
            lbl = f.get("label", ""); val = f.get("value", "")
            if lbl and val:
                fields_html += (
                    f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
                    f'padding:8px 0;border-bottom:1px solid #f0f0f0;font-size:14px;">'
                    f'<span style="font-weight:600;color:#555;">{lbl}</span>'
                    f'<span style="font-weight:700;color:{M};">{val}</span></div>'
                )
        fields_html += '</div>'

    ings = card_data.get("ingredients", [])
    ings_html = ""
    if ings:
        rows = ""
        for idx, ing in enumerate(ings):
            uid = f"nf{abs(hash(ing+str(idx))) % 99999}"
            rows += (
                f'<div id="{uid}" data-checked="0" onclick="'
                f'var c=document.getElementById(\'{uid}c\'),t=document.getElementById(\'{uid}t\');'
                f'if(this.getAttribute(\'data-checked\')==\'1\'){{'
                f'this.setAttribute(\'data-checked\',\'0\');c.style.background=\'#fff\';'
                f'c.style.borderColor=\'{AC}40\';c.innerHTML=\'\';'
                f't.style.textDecoration=\'none\';t.style.opacity=\'1\';this.style.background=\'transparent\';'
                f'}}else{{'
                f'this.setAttribute(\'data-checked\',\'1\');c.style.background=\'{M}\';'
                f'c.style.borderColor=\'{M}\';c.innerHTML=\'✓\';'
                f't.style.textDecoration=\'line-through\';t.style.opacity=\'0.45\';'
                f'this.style.background=\'{AC}10\';'
                f'}}" style="display:flex;align-items:center;gap:10px;padding:7px 10px;'
                f'border-radius:8px;cursor:pointer;user-select:none;margin-bottom:2px;">'
                f'<span id="{uid}c" style="display:inline-flex;align-items:center;justify-content:center;'
                f'min-width:18px;width:18px;height:18px;border:2px solid {AC}40;border-radius:4px;'
                f'background:#fff;color:#fff;font-size:11px;font-weight:900;flex-shrink:0;"></span>'
                f'<span id="{uid}t" style="font-size:14px;color:#333;line-height:1.4;">{ing}</span>'
                f'</div>'
            )
        ings_html = (
            f'<div style="padding:20px 24px;border-bottom:1px solid {AC}20;">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">'
            f'<div style="width:3px;height:20px;background:{M};border-radius:3px;"></div>'
            f'<h3 style="margin:0;font-size:16px;font-weight:800;color:{M};">🧂 Ingredients</h3>'
            f'</div>{rows}</div>'
        )

    steps = card_data.get("instructions", [])
    steps_html = ""
    if steps:
        rows = "".join(
            f'<li style="margin-bottom:8px;list-style:none;">'
            f'<div style="display:flex;align-items:flex-start;gap:12px;padding:12px 14px;'
            f'border-radius:10px;border:1.5px solid {AC}20;background:#fafafa;">'
            f'<span style="display:inline-flex;align-items:center;justify-content:center;'
            f'min-width:28px;width:28px;height:28px;background:{M};color:#fff;'
            f'border-radius:50%;font-size:12px;font-weight:800;flex-shrink:0;">{i+1}</span>'
            f'<span style="font-size:14px;color:#333;line-height:1.6;">{step}</span>'
            f'</div></li>'
            for i, step in enumerate(steps)
        )
        steps_html = (
            f'<div style="padding:20px 24px;">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">'
            f'<div style="width:3px;height:20px;background:{M};border-radius:3px;"></div>'
            f'<h3 style="margin:0;font-size:16px;font-weight:800;color:{M};">👩‍🍳 Instructions</h3>'
            f'</div><ol style="padding:0;margin:0;list-style:none;">{rows}</ol></div>'
        )

    extras = card_data.get("top_attractions", card_data.get("highlights", card_data.get("tips", [])))
    extras_html = ""
    if extras and isinstance(extras, list):
        items = "".join(
            f'<li style="padding:6px 0;font-size:14px;color:#444;border-bottom:1px solid #f0f0f0;">'
            f'<span style="color:{M};font-weight:700;margin-right:6px;">•</span>{item}</li>'
            for item in extras
        )
        extras_html = (
            f'<div style="padding:16px 24px;border-bottom:1px solid {AC}20;">'
            f'<ul style="margin:0;padding:0;list-style:none;">{items}</ul></div>'
        )

    wrap_open  = f'<a href="{article_url}" style="text-decoration:none;display:block;" target="_blank">' if clickable and article_url else ''
    wrap_close = '</a>' if clickable and article_url else ''

    return (
        f'{wrap_open}'
        f'<div id="nf-card" style="border:none;border-radius:20px;overflow:hidden;'
        f'box-shadow:0 16px 48px rgba(0,0,0,0.10),0 4px 12px rgba(0,0,0,0.06);'
        f'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif;'
        f'background:#fff;margin:32px 0;">'
        f'<div style="background:linear-gradient(135deg,{M} 0%,{AC} 100%);padding:24px 28px;text-align:center;">'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;'
        f'color:rgba(255,255,255,0.65);margin-bottom:6px;">✦ Quick Reference ✦</div>'
        f'<h2 style="color:#fff;font-size:22px;margin:0;font-weight:800;">{title}</h2>'
        f'##CARD_IMAGE##'
        f'</div>'
        f'{stats_html}{fields_html}{extras_html}{ings_html}{steps_html}'
        f'<div style="border-top:1px solid {AC}20;padding:14px 24px;text-align:center;background:#fafafa;">'
        f'<span style="font-size:12px;color:#aaa;font-style:italic;">✦ NicheFlow AI</span>'
        f'</div></div>'
        f'{wrap_close}'
    )


# ─────────────────────────────────────────
#  GENERATE ARTICLE
# ─────────────────────────────────────────

def generate_article(title, api_key, user_article_prompt="", user_html_structure="",
                     user_card_prompt="", user_design=None, show_card=True,
                     card_clickable=False, article_url="", use_internal_links=False):
    body_result = [None]; card_result = [None]
    body_error  = [None]; card_error  = [None]

    def _fetch_body():
        try:
            prompt = _build_article_prompt(title, user_article_prompt, user_html_structure,
                                           user_design, show_card, use_internal_links)
            body_result[0] = _call_ai(api_key, prompt, prefer_fast=False)
        except Exception as e:
            body_error[0] = str(e)

    def _fetch_card():
        try:
            if not show_card or not user_card_prompt.strip():
                card_result[0] = "{}"; return
            prompt = _build_card_prompt(title, user_card_prompt, user_design or {})
            card_result[0] = _call_ai(api_key, prompt, prefer_fast=True)
        except Exception as e:
            card_error[0] = str(e)

    t1 = threading.Thread(target=_fetch_body, daemon=True)
    t2 = threading.Thread(target=_fetch_card, daemon=True)
    t1.start(); t2.start()
    t1.join(timeout=120); t2.join(timeout=120)

    if body_error[0]:
        return {"success": False, "error": f"Article generation failed: {body_error[0]}"}
    if not body_result[0]:
        return {"success": False, "error": "Article generation timed out"}

    html = body_result[0]
    html = re.sub(r'^```html?\s*', '', html.strip(), flags=re.IGNORECASE)
    html = re.sub(r'```\s*$', '', html.strip())
    html = _clean_html(html)

    card_data = {}
    if card_result[0] and card_result[0].strip() not in ("{}", ""):
        try:
            raw = re.sub(r'^```json\s*', '', card_result[0].strip(), flags=re.MULTILINE)
            raw = re.sub(r'^```\s*', '', raw, flags=re.MULTILINE).strip()
            s = raw.find('{'); e = raw.rfind('}')
            if s != -1 and e != -1:
                card_data = json.loads(raw[s:e+1])
        except Exception:
            card_data = {}

    if user_design:
        card_data["main_color"]   = user_design.get("main_color", "#333333")
        card_data["accent_color"] = user_design.get("accent_color", "#ea580c")

    if show_card and user_card_prompt.strip() and card_data:
        card_data["card_title"] = card_data.get("card_title", title)
        card_html = _build_card_html(card_data, clickable=card_clickable, article_url=article_url)
        if "##RECIPE_CARD##" in html:
            html = html.replace("##RECIPE_CARD##", card_html)
        else:
            html = html + "\n" + card_html
    else:
        html = html.replace("##RECIPE_CARD##", "")

    html = re.sub(r'##[A-Z0-9_]+##', '', html)
    return {"success": True, "content": html, "parsed": card_data}


# ─────────────────────────────────────────
#  PINTEREST PIN
# ─────────────────────────────────────────

def generate_pinterest_pin(title, article_url, api_key, user_pinterest_prompt):
    try:
        prompt = _build_pinterest_prompt(title, article_url, user_pinterest_prompt)
        raw = _call_ai(api_key, prompt, prefer_fast=True)
        raw = re.sub(r'^```json\s*', '', raw.strip(), flags=re.IGNORECASE | re.MULTILINE)
        raw = re.sub(r'```\s*$', '', raw.strip())
        s = raw.find('{'); e = raw.rfind('}')
        if s != -1 and e != -1:
            data = json.loads(raw[s:e+1])
            return {"success": True, **data}
        return {"success": False, "error": "Could not parse Pinterest response"}
    except Exception as ex:
        return {"success": False, "error": str(ex)}


# ─────────────────────────────────────────
#  MIDJOURNEY
# ─────────────────────────────────────────

def generate_midjourney_image(prompt, goapi_key, log_fn=None):
    headers = {"x-api-key": goapi_key, "Content-Type": "application/json"}
    ar_match = re.search(r'--ar\s+(\d+:\d+)', prompt)
    aspect_ratio = ar_match.group(1) if ar_match else "2:3"

    def log(msg):
        if log_fn: log_fn(msg)

    def _submit(mode):
        return requests.post(
            "https://api.goapi.ai/api/v1/task", headers=headers,
            json={"model": "midjourney", "task_type": "imagine",
                  "input": {"prompt": prompt, "aspect_ratio": aspect_ratio,
                             "process_mode": mode, "skip_prompt_check": False, "bot_id": 0},
                  "config": {"service_mode": "", "webhook_config": {"endpoint": "", "secret": ""}}},
            timeout=30
        )

    def _extract_url(data):
        if not isinstance(data, dict): return None
        for k in ("image_url", "discord_image_url", "cdn_url", "url"):
            v = data.get(k)
            if isinstance(v, str) and v.startswith("http"): return v
        for k in ("image_urls", "temporary_image_urls"):
            v = data.get(k)
            if isinstance(v, list) and v and isinstance(v[0], str) and v[0].startswith("http"):
                return v[0]
        for k in ("output", "result", "data"):
            v = data.get(k)
            if isinstance(v, dict):
                found = _extract_url(v)
                if found: return found
        return None

    try:
        resp = _submit("fast")
        data = resp.json() if resp.status_code == 200 else {}
        if data.get("code") != 200:
            log("  ⚠️ Fast mode failed — trying Relax")
            resp = _submit("relax")
            data = resp.json() if resp.status_code == 200 else {}
            mode_used = "relax"
        else:
            mode_used = "fast"

        if data.get("code") != 200:
            return {"success": False, "error": f"GoAPI: {data.get('message', str(data)[:200])}"}

        task_id = data.get("data", {}).get("task_id")
        if not task_id:
            return {"success": False, "error": "No task_id in response"}

        log(f"  ⏳ MJ submitted [{mode_used}]")
        grid_url = None
        time.sleep(50 if mode_used == "fast" else 90)
        for attempt in range(150):
            try:
                r = requests.get(f"https://api.goapi.ai/api/v1/task/{task_id}",
                                 headers=headers, timeout=15).json()
                td = r.get("data", r)
                status = (td.get("status") or "").lower()
                u = _extract_url(r)
                if u: grid_url = u
                if attempt % 5 == 0: log(f"  🔄 Grid attempt {attempt+1} — {status}")
                if status in ("finished","completed","succeeded","success") and grid_url: break
                if status in ("failed","error","cancelled"):
                    return {"success": False, "error": f"Grid failed: {status}"}
                time.sleep(4)
            except Exception as e:
                log(f"  ⚠️ Poll error: {e}"); time.sleep(4)

        if not grid_url:
            return {"success": False, "error": "Grid timed out"}

        log("  ✅ Grid complete — cropping 4 images...")
        grid_img = Image.open(io.BytesIO(requests.get(grid_url, timeout=30).content)).convert("RGB")
        W, H = grid_img.size; hw, hh = W//2, H//2
        crops = [grid_img.crop((0,0,hw,hh)), grid_img.crop((hw,0,W,hh)),
                 grid_img.crop((0,hh,hw,H)), grid_img.crop((hw,hh,W,H))]
        bytes_list = []
        for i, crop in enumerate(crops):
            out = io.BytesIO(); crop.save(out, format="WEBP", quality=80, method=1)
            bytes_list.append(out.getvalue())
            log(f"  ✂️ Image {i+1}/4 → WebP")
        return {"success": True, "image_bytes": bytes_list}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────
#  IMAGE INJECT & CLEANUP
# ─────────────────────────────────────────

def build_image_html(image_url, alt=""):
    if not image_url or not image_url.startswith("http"): return ""
    return (f'<div style="margin:32px 0 24px 0;clear:both;line-height:0;">'
            f'<img src="{image_url}" alt="{alt}" loading="lazy" '
            f'style="width:100%;border-radius:12px;display:block;height:auto;" /></div>')


def inject_images_into_article(content, image_data, title):
    for ph, idx in {"##IMAGE1##": 1, "##IMAGE2##": 2, "##IMAGE3##": 3, "##IMAGE4##": None}.items():
        if idx is None:
            content = content.replace(ph, ""); continue
        img = image_data[idx] if idx < len(image_data) else None
        content = content.replace(ph, build_image_html(img["url"], title) if (img and img.get("url")) else "")

    featured = image_data[0] if image_data else None
    card_img = (
        f'<div style="margin:0 -28px;line-height:0;overflow:hidden;max-height:260px;">'
        f'<img src="{featured["url"]}" alt="{title}" '
        f'style="width:100%;height:260px;object-fit:cover;display:block;" /></div>'
    ) if (featured and featured.get("url")) else ""
    content = content.replace("##CARD_IMAGE##", card_img)
    content = re.sub(r'##[A-Z0-9_]+##', '', content)

    def _valid(tag):
        src = re.search(r'src=[\'\"](.*?)[\'\"]', tag)
        return src and src.group(1).startswith('https://')

    content = re.sub(r'<div[^>]*>\s*<img[^>]*/?\s*>\s*</div>',
                     lambda m: m.group(0) if _valid(m.group(0)) else "",
                     content, flags=re.DOTALL|re.IGNORECASE)
    content = re.sub(r'<img[^>]*/?>',
                     lambda m: m.group(0) if _valid(m.group(0)) else "",
                     content, flags=re.IGNORECASE)
    content = re.sub(r'alt="[^"]{0,3}"', f'alt="{title}"', content)
    return content


# ─────────────────────────────────────────
#  WORDPRESS
# ─────────────────────────────────────────

def parse_wp_credentials(wp_url, wp_password):
    base_url = re.sub(r'/wp-json.*$', '', wp_url.strip().rstrip("/"))
    base_url = re.sub(r'/wp-admin.*$', '', base_url)
    if ":" in wp_password:
        i = wp_password.index(":")
        u, p = wp_password[:i].strip(), wp_password[i+1:].strip()
        if u and p: return base_url, u, p
    return base_url, "", wp_password.strip()


def upload_image_to_wordpress(image_bytes, filename, wp_url, wp_user, wp_password):
    creds = base64.b64encode(f"{wp_user}:{wp_password}".encode()).decode()
    try:
        resp = requests.post(f"{wp_url.rstrip('/')}/wp-json/wp/v2/media",
                             headers={"Authorization": f"Basic {creds}",
                                      "Content-Disposition": f'attachment; filename="{filename}"',
                                      "Content-Type": "image/webp"},
                             data=image_bytes, timeout=60)
        if resp.status_code in [200, 201]:
            d = resp.json()
            return {"success": True, "media_id": d.get("id"), "url": d.get("source_url", "")}
        return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def publish_to_wordpress(title, content, wp_url, wp_password, status="draft",
                          meta_description="", featured_media_id=None, category_ids=None):
    wp_url_clean, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    creds = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    post_data = {"title": title, "content": content, "status": status, "format": "standard"}
    if category_ids: post_data["categories"] = category_ids
    if meta_description:
        post_data["meta"] = {"_yoast_wpseo_metadesc": meta_description, "_yoast_wpseo_title": title}
    if featured_media_id: post_data["featured_media"] = featured_media_id
    try:
        resp = requests.post(f"{wp_url_clean}/wp-json/wp/v2/posts",
                             headers={"Authorization": f"Basic {creds}", "Content-Type": "application/json"},
                             json=post_data, timeout=30)
        if resp.status_code in [200, 201]:
            d = resp.json()
            return {"success": True, "post_id": d.get("id"), "post_url": d.get("link",""), "status": d.get("status")}
        return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to WordPress. Check your URL."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def make_slug(title):
    s = re.sub(r'[^a-z0-9\s-]', '', title.lower())
    return re.sub(r'\s+', '-', s.strip())[:60]


# ─────────────────────────────────────────
#  INTERNAL LINKS
# ─────────────────────────────────────────

def fetch_internal_links(wp_url, wp_password, max_posts=100):
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    creds = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    STOP = {"the","and","for","with","this","that","from","your","are","our","how","you","can",
            "was","its","all","but","not","have","has","had","what","when","make","made","easy","best"}
    posts = []
    try:
        page = 1
        while len(posts) < max_posts:
            resp = requests.get(f"{base_url}/wp-json/wp/v2/posts",
                                headers={"Authorization": f"Basic {creds}"},
                                params={"status": "publish","per_page": 50,"page": page,
                                        "_fields": "id,title,link,slug"}, timeout=20)
            if resp.status_code != 200: break
            batch = resp.json()
            if not batch: break
            for p in batch:
                t = re.sub(r'<[^>]+>', '', str(p.get("title",{}).get("rendered",""))).strip()
                u = p.get("link","")
                if not t or not u: continue
                words = [w for w in re.findall(r'[a-zA-Z]{3,}', t.lower()) if w not in STOP]
                posts.append({"title": t, "url": u, "slug": p.get("slug",""), "keywords": words})
            if len(batch) < 50: break
            page += 1
    except Exception as e:
        print(f"fetch_internal_links error: {e}")
    return posts


def inject_internal_links(html, posts, current_title, max_links=4, main_color="#ea580c"):
    if not posts or not html: return html
    STOP = {"the","and","for","with","this","that","from","your","are","our","how","you","can",
            "was","easy","best","recipe","meal","prep","fresh","quick","simple","great","good"}
    curr = re.sub(r'[^a-z0-9]+', '-', current_title.lower()).strip('-')
    plain = re.sub(r'<[^>]+>', ' ', html).lower()

    def find_anchor(pt):
        words = [w for w in re.findall(r'[A-Za-z]{3,}', pt) if w.lower() not in STOP]
        for n in (3,2,1):
            for i in range(len(words)-n+1):
                ph = " ".join(words[i:i+n])
                if re.search(r'\b'+re.escape(ph)+r'\b', plain, re.IGNORECASE): return ph
        return None

    link_map = {}; seen = set()
    for post in posts:
        if len(link_map) >= max_links*2: break
        if curr in post.get("slug","") or current_title.lower()[:20] in post.get("title","").lower(): continue
        a = find_anchor(post.get("title",""))
        if a and a.lower() not in seen:
            link_map[a] = post["url"]; seen.add(a.lower())

    if not link_map: return html
    added = [0]; used = set()

    def linkify(p):
        if added[0] >= max_links or '<a ' in p: return p
        if len(re.sub(r'<[^>]+>','',p).strip()) < 60: return p
        for anchor, url in link_map.items():
            if added[0] >= max_links or anchor.lower() in used: continue
            pat = re.compile(r'\b'+re.escape(anchor)+r'\b', re.IGNORECASE)
            if not pat.search(re.sub(r'<[^>]+>','',p)): continue
            def _rep(m, _u=url, _a=anchor):
                return (f'<a href="{_u}" title="{_a}" rel="noopener" '
                        f'style="color:{main_color};text-decoration:underline;font-weight:600;">'
                        f'{m.group(0)}</a>')
            parts=[]; last=0; replaced=False
            for tm in re.finditer(r'<[^>]+>', p):
                chunk = p[last:tm.start()]
                if not replaced:
                    nc, n = pat.subn(_rep, chunk, count=1)
                    if n: replaced=True; chunk=nc
                parts.append(chunk); parts.append(tm.group(0)); last=tm.end()
            chunk=p[last:]
            if not replaced:
                nc, n = pat.subn(_rep, chunk, count=1)
                if n: replaced=True; chunk=nc
            parts.append(chunk)
            if replaced:
                p=''.join(parts); used.add(anchor.lower()); added[0]+=1
        return p

    split = html.split('<div id="nf-card"', 1)
    art = split[0]
    card = ('<div id="nf-card"'+split[1]) if len(split)>1 else ""
    art = re.sub(r'(<p[^>]*>)(.*?)(</p>)',
                 lambda m: m.group(1)+linkify(m.group(2))+m.group(3),
                 art, flags=re.DOTALL)
    return art+card


# ─────────────────────────────────────────
#  FULL PIPELINE
# ─────────────────────────────────────────

def run_full_pipeline(title, settings, log_fn=None, internal_links=None):
    import queue as _q
    q = _q.Queue()
    def log(msg): q.put(str(msg))
    def flush():
        while not q.empty():
            try:
                m = q.get_nowait()
                if log_fn: log_fn(m)
            except: pass

    groq_key       = settings.get("groq_key","")
    goapi_key      = settings.get("goapi_key","")
    wp_url         = settings.get("wp_url","")
    wp_password    = settings.get("wp_password","")
    publish_status = settings.get("publish_status","draft")
    mj_template    = settings.get("mj_template","")
    use_images     = settings.get("use_images", True)
    show_card      = settings.get("show_card", True)
    card_clickable = settings.get("card_clickable", False)
    use_int_links  = settings.get("use_internal_links", False)
    max_links      = settings.get("max_links", 4)
    category_ids   = settings.get("category_ids", None)
    user_article_prompt = settings.get("user_article_prompt","")
    user_html_structure = settings.get("user_html_structure","")
    user_card_prompt    = settings.get("user_card_prompt","")
    user_design         = settings.get("user_design",{})

    wp_url_clean, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    slug = make_slug(title)

    mj_prompt = ""
    if use_images and goapi_key:
        if mj_template and "{recipe_name}" in mj_template:
            mj_prompt = mj_template.replace("{recipe_name}", title)
        elif mj_template:
            mj_prompt = f"{mj_template} {title}"
        else:
            mj_prompt = f"{title}, professional photography, natural light --ar 2:3 --v 6.1"

    log(f"✏️ Generating article: {title}")
    flush()

    art_result = [None]
    image_results = [None]*4

    def _gen_art():
        try:
            art_result[0] = generate_article(
                title=title, api_key=groq_key,
                user_article_prompt=user_article_prompt,
                user_html_structure=user_html_structure,
                user_card_prompt=user_card_prompt,
                user_design=user_design, show_card=show_card,
                card_clickable=card_clickable, article_url="",
                use_internal_links=use_int_links,
            )
            log("✅ Article ready" if art_result[0]["success"] else f"❌ {art_result[0]['error']}")
        except Exception as e:
            log(f"💥 Article error: {e}"); art_result[0]={"success":False,"error":str(e)}

    def _gen_imgs():
        if not use_images or not goapi_key or not mj_prompt:
            for i in range(4): image_results[i]={"url":None,"media_id":None}
            return
        try:
            log("  🎨 Generating images...")
            mj = generate_midjourney_image(mj_prompt, goapi_key, log_fn=log)
            if not mj["success"]:
                log(f"  ❌ Images failed: {mj['error']}")
                for i in range(4): image_results[i]={"url":None,"media_id":None}
                return
            bytes_list = mj.get("image_bytes",[])
            labels = ["featured","closeup","lifestyle","detail"]
            def _up(i, webp, lbl):
                r = upload_image_to_wordpress(webp, f"{slug}-{lbl}.webp", wp_url_clean, wp_user, wp_pass)
                image_results[i] = {"url":r.get("url"),"media_id":r.get("media_id")} if r["success"] else {"url":None,"media_id":None}
                log(f"  {'✅' if r['success'] else '❌'} Image {i+1} ({lbl})")
            ts = [threading.Thread(target=_up, args=(i,webp,lbl), daemon=True)
                  for i,(webp,lbl) in enumerate(zip(bytes_list,labels))]
            for t in ts: t.start()
            for i in range(len(bytes_list),4): image_results[i]={"url":None,"media_id":None}
            for t in ts: t.join(timeout=120)
        except Exception as e:
            log(f"  💥 Image error: {e}")
            for i in range(4):
                if image_results[i] is None: image_results[i]={"url":None,"media_id":None}

    ta = threading.Thread(target=_gen_art, daemon=True)
    ti = threading.Thread(target=_gen_imgs, daemon=True)
    ta.start(); ti.start()
    deadline = time.time()+600
    while any(t.is_alive() for t in [ta,ti]):
        flush()
        if time.time()>deadline: log("⚠️ Timeout"); break
        time.sleep(2)
    for t in [ta,ti]: t.join(timeout=5)
    flush()

    art = art_result[0]
    if not art or not art["success"]:
        return {"success":False,"error": art["error"] if art else "Thread did not complete"}

    done = sum(1 for r in image_results if r and r.get("url"))
    log(f"✅ {done}/4 images ready")

    log("🔧 Injecting images...")
    final = inject_images_into_article(art["content"], image_results, title)

    if use_int_links:
        _links = internal_links
        if not _links and wp_url and wp_password:
            log("🔗 Fetching internal links...")
            try: _links = fetch_internal_links(wp_url, wp_password); log(f"🔗 {len(_links)} posts loaded")
            except Exception as le: log(f"⚠️ Links error: {le}")
        if _links:
            mc = (user_design or {}).get("main_color","#ea580c")
            final = inject_internal_links(final, _links, title, max_links=max_links, main_color=mc)

    log("📤 Publishing to WordPress...")
    fid = image_results[0]["media_id"] if image_results[0] and image_results[0].get("media_id") else None
    meta = f"Read about {title} — expert insights, tips, and complete guide."[:155]
    pub = publish_to_wordpress(title=title, content=final, wp_url=wp_url, wp_password=wp_password,
                               status=publish_status, meta_description=meta,
                               featured_media_id=fid, category_ids=category_ids)
    log(f"{'🎉 Published! → '+pub.get('post_url','') if pub['success'] else '❌ '+pub['error']}")
    return {**pub, "image_count": done}


# ─────────────────────────────────────────
#  TEST FUNCTIONS
# ─────────────────────────────────────────

def test_groq_key(api_key):
    try:
        if not api_key.startswith("gsk_"):
            return {"success":False,"message":"❌ Must start with gsk_ — get free key at console.groq.com"}
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
                             headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
                             json={"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"Say OK"}],"max_tokens":5},
                             timeout=15)
        if resp.status_code==200: return {"success":True,"message":"✅ Groq key works! 14,400 req/day free"}
        if resp.status_code==401: return {"success":False,"message":"❌ Invalid Groq key"}
        if resp.status_code==429: return {"success":True,"message":"✅ Groq key valid (rate limited — wait 1 min)"}
        return {"success":False,"message":f"❌ Groq error: {resp.status_code}"}
    except Exception as e:
        return {"success":False,"message":str(e)}


def test_goapi_key(api_key):
    try:
        resp = requests.get("https://api.goapi.ai/api/v1/task",
                            headers={"x-api-key":api_key}, timeout=10)
        if resp.status_code in (200,405): return {"success":True,"message":"✅ GoAPI key accepted"}
        if resp.status_code==401: return {"success":False,"message":"❌ Invalid GoAPI key"}
        return {"success":True,"message":f"✅ GoAPI key accepted (HTTP {resp.status_code})"}
    except Exception as e:
        return {"success":False,"message":f"GoAPI error: {str(e)}"}


def test_wordpress(wp_url, wp_password):
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    if not wp_user:
        return {"success":False,"message":"❌ No username found. Use format: Username:app-password"}
    try:
        creds = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
        resp = requests.get(f"{base_url}/wp-json/wp/v2/users/me",
                            headers={"Authorization":f"Basic {creds}"}, timeout=10)
        if resp.status_code==200:
            return {"success":True,"message":f"✅ Connected as: {resp.json().get('name',wp_user)}"}
        return {"success":False,"message":f"❌ HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success":False,"message":f"❌ Error: {str(e)}"}


def fetch_wp_categories(wp_url, wp_password):
    base_url, wp_user, wp_pass = parse_wp_credentials(wp_url, wp_password)
    creds = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    cats = []
    try:
        resp = requests.get(f"{base_url}/wp-json/wp/v2/categories",
                            headers={"Authorization":f"Basic {creds}"},
                            params={"per_page":100,"_fields":"id,name,count"}, timeout=15)
        if resp.status_code==200:
            cats = sorted([{"id":c["id"],"name":c["name"],"count":c.get("count",0)}
                           for c in resp.json()], key=lambda x: x["name"])
    except Exception as e:
        print(f"fetch_wp_categories error: {e}")
    return cats