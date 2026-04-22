# -*- coding: utf-8 -*-
"""NicheFlow AI — generator.py
FIXES:
- Pollinations: retry logic + proper content-type check + fallback download
- _gen_single: if raw_bytes missing but URL exists, download separately
- Better logging so user sees exactly what is happening
- Featured image: robust media_id extraction
"""
import requests, json, base64, re, time, io, threading
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
{"pin_title":"[max 60 chars keyword-rich]","pin_description":"[max 150 chars with CTA Save this!]","alt_text":"[1 descriptive sentence]","hashtags":["tag1","tag2","tag3","tag4","tag5"],"hook_title":"[EXACTLY 4 words, punchy hook for pin image]"}"""

DEFAULT_PIN_IMAGE_PROMPT = """background_color:#1a1a2e overlay_opacity:0.55 title_color:#ffffff title_size:72 subtitle_color:#f0f0f0 subtitle_size:32 canvas_width:1000 canvas_height:1500 title_position:bottom logo_text:nicheflow.ai gradient:true gradient_color:#6366f1"""


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


def parse_pin_image_prompt(prompt_str):
    defaults = {
        "background_color": "#1a1a2e",
        "overlay_opacity": 0.55,
        "title_color": "#ffffff",
        "title_size": 72,
        "subtitle_color": "#f0f0f0",
        "subtitle_size": 32,
        "canvas_width": 1000,
        "canvas_height": 1500,
        "title_position": "bottom",
        "logo_text": "",
        "gradient": True,
        "gradient_color": "#6366f1",
    }
    if not prompt_str or not prompt_str.strip():
        return defaults
    cfg = dict(defaults)
    for part in prompt_str.strip().split():
        if ":" in part:
            k, v = part.split(":", 1)
            k = k.strip(); v = v.strip()
            if k in ("background_color","title_color","subtitle_color","gradient_color"):
                cfg[k] = v
            elif k == "overlay_opacity":
                try: cfg[k] = float(v)
                except: pass
            elif k in ("title_size","subtitle_size","canvas_width","canvas_height"):
                try: cfg[k] = int(v)
                except: pass
            elif k == "title_position":
                if v in ("top","center","bottom"): cfg[k] = v
            elif k == "logo_text":
                cfg[k] = v
            elif k == "gradient":
                cfg[k] = v.lower() in ("true","1","yes")
    return cfg


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c*2 for c in hex_color)
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (255, 255, 255)


def wrap_text(text, max_chars_per_line=18):
    words = text.split()
    lines = []
    current = []
    current_len = 0
    for word in words:
        if current_len + len(word) + (1 if current else 0) <= max_chars_per_line:
            current.append(word)
            current_len += len(word) + (1 if len(current) > 1 else 0)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
    if current:
        lines.append(" ".join(current))
    return lines


def generate_pin_image_with_pillow(hook_title, image_bytes_list, pin_image_prompt="", article_title="", log_fn=None):
    def log(m):
        if log_fn: log_fn(m)
    try:
        cfg = parse_pin_image_prompt(pin_image_prompt)
        W = cfg["canvas_width"]
        H = cfg["canvas_height"]
        bg_color = hex_to_rgb(cfg["background_color"])
        title_color = hex_to_rgb(cfg["title_color"])
        subtitle_color = hex_to_rgb(cfg["subtitle_color"])
        overlay_opacity = min(1.0, max(0.0, cfg["overlay_opacity"]))
        gradient_color = hex_to_rgb(cfg["gradient_color"])
        use_gradient = cfg["gradient"]
        title_position = cfg["title_position"]
        logo_text = cfg.get("logo_text", "")

        canvas = Image.new("RGBA", (W, H), (*bg_color, 255))

        bg_image_used = False
        for img_bytes in image_bytes_list:
            if not img_bytes:
                continue
            try:
                bg_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                img_w, img_h = bg_img.size
                target_ratio = W / H
                img_ratio = img_w / img_h
                if img_ratio > target_ratio:
                    new_w = int(img_h * target_ratio)
                    left = (img_w - new_w) // 2
                    bg_img = bg_img.crop((left, 0, left + new_w, img_h))
                else:
                    new_h = int(img_w / target_ratio)
                    top = (img_h - new_h) // 2
                    bg_img = bg_img.crop((0, top, img_w, top + new_h))
                bg_img = bg_img.resize((W, H), Image.LANCZOS)
                bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=2))
                canvas = bg_img
                bg_image_used = True
                log("  🖼️ Using article image as pin background")
                break
            except Exception as e:
                log(f"  ⚠️ Could not use image as background: {e}")
                continue

        if not bg_image_used:
            log("  🎨 Using solid color background for pin")

        canvas = canvas.convert("RGBA")
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, int(overlay_opacity * 255)))
        canvas = Image.alpha_composite(canvas, overlay)

        if use_gradient or title_position == "bottom":
            gradient_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            grad_draw = ImageDraw.Draw(gradient_overlay)
            grad_height = int(H * 0.55)
            grad_start = H - grad_height
            for y in range(grad_start, H):
                alpha = int(220 * ((y - grad_start) / grad_height))
                r, g, b = gradient_color if use_gradient else (0, 0, 0)
                blend = (y - grad_start) / grad_height
                r2 = int(r * (1 - blend * 0.7))
                g2 = int(g * (1 - blend * 0.7))
                b2 = int(b * (1 - blend * 0.7))
                grad_draw.line([(0, y), (W, y)], fill=(r2, g2, b2, alpha))
            canvas = Image.alpha_composite(canvas, gradient_overlay)

        draw = ImageDraw.Draw(canvas)
        title_font = None
        subtitle_font = None
        logo_font = None
        font_size = cfg["title_size"]
        subtitle_size = cfg["subtitle_size"]

        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        ]
        regular_font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]

        for fp in font_paths:
            try:
                title_font = ImageFont.truetype(fp, font_size)
                logo_font = ImageFont.truetype(fp, 28)
                break
            except: continue

        for fp in regular_font_paths:
            try:
                subtitle_font = ImageFont.truetype(fp, subtitle_size)
                break
            except: continue

        if title_font is None: title_font = ImageFont.load_default()
        if subtitle_font is None: subtitle_font = ImageFont.load_default()
        if logo_font is None: logo_font = ImageFont.load_default()

        hook = hook_title.upper() if hook_title else article_title[:40].upper()
        hook_words = hook.split()[:4]
        hook_lines = wrap_text(" ".join(hook_words), max_chars_per_line=14)
        subtitle = article_title[:60] if article_title else ""
        subtitle_lines = wrap_text(subtitle, max_chars_per_line=28)

        padding = 48
        line_spacing = int(font_size * 1.15)
        subtitle_line_spacing = int(subtitle_size * 1.3)
        total_hook_h = len(hook_lines) * line_spacing
        total_sub_h = len(subtitle_lines) * subtitle_line_spacing if subtitle_lines else 0
        total_text_h = total_hook_h + (20 if subtitle_lines else 0) + total_sub_h

        if title_position == "bottom":
            text_y_start = H - padding - total_text_h - (40 if logo_text else 0)
        elif title_position == "top":
            text_y_start = padding + (40 if logo_text else 0)
        else:
            text_y_start = (H - total_text_h) // 2

        current_y = text_y_start
        for line in hook_lines:
            shadow_offset = 3
            try:
                bbox = draw.textbbox((0, 0), line, font=title_font)
                text_w = bbox[2] - bbox[0]
            except:
                text_w = len(line) * (font_size // 2)
            x = (W - text_w) // 2
            draw.text((x + shadow_offset, current_y + shadow_offset), line, font=title_font, fill=(0, 0, 0, 160))
            draw.text((x, current_y), line, font=title_font, fill=(*title_color, 255))
            current_y += line_spacing

        if subtitle_lines:
            current_y += 20
            for line in subtitle_lines:
                try:
                    bbox = draw.textbbox((0, 0), line, font=subtitle_font)
                    text_w = bbox[2] - bbox[0]
                except:
                    text_w = len(line) * (subtitle_size // 2)
                x = (W - text_w) // 2
                draw.text((x + 2, current_y + 2), line, font=subtitle_font, fill=(0, 0, 0, 120))
                draw.text((x, current_y), line, font=subtitle_font, fill=(*subtitle_color, 220))
                current_y += subtitle_line_spacing

        line_y = text_y_start - 20
        line_w = 80
        line_x = (W - line_w) // 2
        accent_color = hex_to_rgb(cfg["gradient_color"])
        draw.rectangle([(line_x, line_y), (line_x + line_w, line_y + 4)], fill=(*accent_color, 255))

        if logo_text:
            try:
                bbox = draw.textbbox((0, 0), logo_text, font=logo_font)
                logo_w = bbox[2] - bbox[0]
            except:
                logo_w = len(logo_text) * 14
            logo_x = (W - logo_w) // 2
            draw.text((logo_x, padding), logo_text, font=logo_font, fill=(*subtitle_color, 180))

        final = canvas.convert("RGB")
        buf = io.BytesIO()
        final.save(buf, format="WEBP", quality=85, method=4)
        result_bytes = buf.getvalue()
        log(f"  ✅ Pin image generated ({W}x{H}px, {len(result_bytes)//1024}KB)")
        return result_bytes

    except Exception as e:
        log(f"  ❌ Pin image generation failed: {e}")
        return None


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
    def log(m):
        if log_fn: log_fn(m)
    headers = {"x-api-key": goapi_key, "Content-Type": "application/json"}
    try:
        resp = requests.post("https://api.goapi.ai/api/v1/task", headers=headers,
            json={"model":"midjourney","task_type":"imagine","input":{"prompt":prompt,"process_mode":"fast"}}, timeout=30)
        if resp.status_code != 200: return {"url":None,"error":f"MJ error {resp.status_code}"}
        task_id = resp.json().get("data",{}).get("task_id")
        if not task_id: return {"url":None,"error":"No task_id"}
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
                # Download IMMEDIATELY — GoAPI CDN URLs expire within seconds (403 after delay)
                log("  ✅ MJ ready — downloading now before URL expires...")
                try:
                    for attempt_headers in [
                        {"User-Agent":"Mozilla/5.0","Referer":"https://goapi.ai"},
                        {"User-Agent":"Mozilla/5.0 (compatible)","Accept":"image/*,*/*"},
                        {},
                    ]:
                        dl_resp = requests.get(url, timeout=90, headers=attempt_headers)
                        if dl_resp.status_code == 200 and len(dl_resp.content) > 1000:
                            log(f"  ✅ MJ image downloaded ({len(dl_resp.content)//1024}KB)")
                            return {"url":url,"raw_bytes":dl_resp.content,"error":None}
                        log(f"  ⚠️ MJ download attempt failed: HTTP {dl_resp.status_code}")
                    log("  ⚠️ All MJ download attempts failed — returning URL only")
                    return {"url":url,"raw_bytes":None,"error":None}
                except Exception as dl_e:
                    log(f"  ⚠️ MJ download exception: {dl_e}")
                    return {"url":url,"raw_bytes":None,"error":None}
            elif status == "failed":
                err = data.get("error",{}).get("message","Unknown")
                if "fast" in err.lower() or "quota" in err.lower():
                    log("  ⚠️ Fast quota, trying relax...")
                    resp2 = requests.post("https://api.goapi.ai/api/v1/task", headers=headers,
                        json={"model":"midjourney","task_type":"imagine","input":{"prompt":prompt,"process_mode":"relax"}}, timeout=30)
                    if resp2.status_code == 200: task_id = resp2.json().get("data",{}).get("task_id",task_id)
                    continue
                return {"url":None,"error":err}
            elif attempt % 5 == 0: log(f"  ⏳ Generating... ({attempt*3}s)")
        return {"url":None,"error":"Timeout 270s"}
    except Exception as e: return {"url":None,"error":str(e)}


def generate_pollinations_image(prompt, width=1024, height=1024, log_fn=None):
    """
    FIXED: Added retry logic and proper content-type validation.
    Pollinations sometimes returns HTML with status 200 — this handles that.
    """
    def log(m):
        if log_fn: log_fn(m)

    safe_prompt = requests.utils.quote(prompt[:400])
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={width}&height={height}&nologo=true&seed={int(time.time())}"

    # Try up to 3 times — Pollinations is flaky
    for attempt in range(3):
        try:
            if attempt > 0:
                log(f"  🔄 Pollinations retry {attempt+1}/3...")
                time.sleep(3 * attempt)

            resp = requests.get(url, timeout=90, headers={"User-Agent": "Mozilla/5.0"})

            if resp.status_code != 200:
                log(f"  ⚠️ Pollinations status {resp.status_code}, retrying...")
                continue

            content_type = resp.headers.get("content-type", "").lower()
            content = resp.content

            # Check if we got an actual image (not HTML error page)
            if content_type.startswith("image/"):
                log(f"  ✅ Pollinations image received ({len(content)//1024}KB)")
                return {"url": url, "raw_bytes": content, "error": None}

            # Sometimes Pollinations returns image data with wrong content-type
            # Try to open it as an image anyway
            if len(content) > 5000:  # real images are > 5KB
                try:
                    Image.open(io.BytesIO(content))
                    log(f"  ✅ Pollinations image received (content-type mismatch but valid image)")
                    return {"url": url, "raw_bytes": content, "error": None}
                except:
                    pass

            log(f"  ⚠️ Pollinations returned non-image content ({content_type}), retrying...")
            continue

        except requests.exceptions.Timeout:
            log(f"  ⚠️ Pollinations timeout (attempt {attempt+1})")
            continue
        except Exception as e:
            log(f"  ⚠️ Pollinations error: {e}")
            continue

    log(f"  ❌ Pollinations failed after 3 attempts")
    return {"url": None, "raw_bytes": None, "error": "Failed after 3 attempts"}


def download_image_bytes(image_url, log_fn=None):
    """Download image from URL and return raw bytes."""
    def log(m):
        if log_fn: log_fn(m)
    try:
        resp = requests.get(image_url, timeout=60, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            return resp.content
        log(f"  ⚠️ Download failed: HTTP {resp.status_code}")
        return None
    except Exception as e:
        log(f"  ⚠️ Download error: {e}")
        return None


def crop_and_convert_to_webp(raw_bytes_or_url, max_width=1920, target_ratio=None, log_fn=None):
    """
    Download (if URL), crop to target ratio if specified, convert to WebP.
    Returns WebP bytes or None.
    """
    def log(m):
        if log_fn: log_fn(m)
    try:
        if isinstance(raw_bytes_or_url, str):
            raw = download_image_bytes(raw_bytes_or_url, log_fn)
        else:
            raw = raw_bytes_or_url
        if not raw:
            log("  ⚠️ No raw bytes to convert")
            return None

        img = Image.open(io.BytesIO(raw)).convert("RGB")

        if target_ratio:
            tw, th = target_ratio
            ratio = tw / th
            img_w, img_h = img.size
            img_ratio = img_w / img_h
            if img_ratio > ratio:
                new_w = int(img_h * ratio)
                left = (img_w - new_w) // 2
                img = img.crop((left, 0, left + new_w, img_h))
            elif img_ratio < ratio:
                new_h = int(img_w / ratio)
                top = (img_h - new_h) // 2
                img = img.crop((0, top, img_w, top + new_h))

        if img.width > max_width:
            ratio_scale = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio_scale)), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=82, method=2)
        return buf.getvalue()
    except Exception as e:
        log(f"  ⚠️ WebP conversion failed: {e}")
        return None


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
        resp = requests.post(f"{base_url}/wp-json/wp/v2/media", headers=headers, data=image_bytes, timeout=120)
        if resp.status_code in (200, 201):
            data = resp.json()
            media_id = data.get("id")
            source_url = data.get("source_url","")
            log(f"  ✅ Uploaded {filename} → media_id={media_id}, url={source_url[:50]}")
            return {"success":True,"media_id":media_id,"url":source_url,"error":None}
        err_text = resp.text[:300]
        log(f"  ❌ WP upload failed {resp.status_code}: {err_text}")
        return {"success":False,"media_id":None,"url":None,"error":f"WP {resp.status_code}: {err_text}"}
    except Exception as e:
        log(f"  ❌ WP upload exception: {e}")
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


def parse_wp_credentials(wp_url, wp_password):
    base_url = wp_url.rstrip("/")
    if ":" in wp_password:
        idx = wp_password.index(":")
        wp_user = wp_password[:idx].strip()
        wp_pass = wp_password[idx+1:].strip()
    else:
        wp_user = ""; wp_pass = wp_password.strip()
    return base_url, wp_user, wp_pass


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


def inject_images_into_article(html, image_results, title, log_fn=None):
    """
    Replace ##IMAGE1## ##IMAGE2## ##IMAGE3## with actual img tags.
    image_results[0] = featured, image_results[1,2,3] = body images
    """
    def log(m):
        if log_fn: log_fn(m)

    placeholders = ["##IMAGE1##", "##IMAGE2##", "##IMAGE3##"]
    for i, ph in enumerate(placeholders):
        img_idx = i + 1  # 1, 2, 3
        img_data = image_results[img_idx] if img_idx < len(image_results) else None

        if img_data and img_data.get("url"):
            img_url = img_data["url"]
            img_tag = (
                f'<figure style="margin:28px auto;text-align:center;max-width:720px;">'
                f'<img src="{img_url}" alt="{title}" loading="lazy" '
                f'style="width:100%;border-radius:14px;box-shadow:0 4px 24px rgba(0,0,0,0.12);display:block;" />'
                f'</figure>'
            )
            html = html.replace(ph, img_tag)
            log(f"  ✅ {ph} → image injected")
        else:
            html = html.replace(ph, "")
            log(f"  ⚠️ {ph} → no image, placeholder removed")
    return html


def generate_pin_content(api_key, title, article_url, pinterest_prompt=""):
    try:
        prompt = (pinterest_prompt.strip() if pinterest_prompt.strip() else DEFAULT_PINTEREST_PROMPT).replace("{title}",title).replace("{url}",article_url)
        raw = ai_call(api_key, prompt, prefer_fast=True)
        data = parse_json_response(raw)
        hook = data.get("hook_title", title)
        hook_words = hook.split()
        if len(hook_words) > 4:
            hook = " ".join(hook_words[:4])
        elif len(hook_words) < 4:
            title_words = title.split()
            while len(hook_words) < 4 and title_words:
                hook_words.append(title_words.pop(0))
            hook = " ".join(hook_words[:4])
        return {
            "success":True,
            "pin_title":data.get("pin_title",title[:60]),
            "pin_description":data.get("pin_description",""),
            "alt_text":data.get("alt_text",title),
            "hashtags":data.get("hashtags",[]),
            "hook_title": hook,
        }
    except Exception as e:
        return {
            "success":False,
            "pin_title":title[:60],
            "pin_description":f"Check this out! {article_url}",
            "alt_text":title,
            "hashtags":[],
            "hook_title": " ".join(title.split()[:4]),
            "error":str(e),
        }


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


def run_pinterest_bot(api_key, access_token, articles, board_ids,
    pinterest_prompt="", pin_delay_min=0, pin_image_prompt="",
    wp_url="", wp_password="", log_fn=None):
    def log(m):
        if log_fn: log_fn(m)
    results = []
    for art in articles:
        title = art.get("title","")
        url = art.get("post_url","")
        featured_img = art.get("featured_image_url","")
        body_images_bytes = art.get("body_images_bytes", [])

        log(f"📌 {title}")
        if not url:
            log("  ✗ No URL")
            results.append({"title":title,"status":"failed","error":"No URL"})
            continue

        log("  ✦ Generating pin content...")
        pin_data = generate_pin_content(api_key, title, url, pinterest_prompt)
        log(f"  ✓ Hook: \"{pin_data['hook_title']}\" | Title: {pin_data['pin_title']}")

        pin_image_url = featured_img
        log("  🎨 Generating Pinterest pin image...")
        pin_img_bytes = generate_pin_image_with_pillow(
            hook_title=pin_data["hook_title"],
            image_bytes_list=body_images_bytes,
            pin_image_prompt=pin_image_prompt,
            article_title=title,
            log_fn=log,
        )

        if pin_img_bytes and wp_url and wp_password:
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]
            pin_fname = f"{slug}-pin.webp"
            up = upload_image_to_wordpress(wp_url, wp_password, pin_img_bytes, pin_fname, log)
            if up.get("success") and up.get("url"):
                pin_image_url = up["url"]
                log(f"  ✅ Pin image uploaded → {pin_image_url[:60]}")
            else:
                log(f"  ⚠️ Pin image upload failed, using featured image as fallback")
        elif pin_img_bytes:
            log("  ⚠️ No WP credentials for pin image upload")

        if pin_delay_min > 0:
            log(f"  ⏱ Waiting {pin_delay_min}m...")
            time.sleep(pin_delay_min * 60)

        article_results = []
        for board_id in board_ids:
            log(f"  → Board {board_id}...")
            r = create_pinterest_pin(
                access_token, board_id,
                pin_data["pin_title"],
                pin_data["pin_description"],
                pin_data["alt_text"],
                url,
                pin_image_url or "",
            )
            log(f"  {'✅' if r['success'] else '❌'} {r.get('pin_id') or r.get('error')}")
            article_results.append({"board_id":board_id,**r})

        results.append({
            "title": title,
            "pin_title": pin_data["pin_title"],
            "pin_description": pin_data.get("pin_description",""),
            "alt_text": pin_data.get("alt_text",""),
            "hook_title": pin_data.get("hook_title",""),
            "pin_image_url": pin_image_url,
            "boards": article_results,
            "status": "sent" if any(r["success"] for r in article_results) else "failed",
        })
    return results


def run_full_pipeline(title, gemini_key, goapi_key="", wp_url="", wp_password="", publish_status="publish",
    mj_template="", custom_prompt="", card_prompt="", show_card=True, use_images=False,
    use_pollinations=False, pollinations_prompt="", internal_links=None, category_ids=None,
    max_links=4, use_internal_links=True, log_fn=None):

    def log(msg):
        if log_fn: log_fn(msg)

    art_result = [None]
    card_result = [None]
    # image_results: list of 4 dicts {url, media_id, raw_bytes}
    # index 0 = featured, 1/2/3 = body images
    image_results = [{"url":None,"media_id":None,"raw_bytes":None} for _ in range(4)]
    all_threads = []
    _log_lock = threading.Lock()

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
            safe_log("ℹ️ Images disabled — toggle 'Generate Images' in the Generate page to enable")
            return
        if not use_pollinations and not goapi_key:
            safe_log("⚠️ No image source — enable Pollinations in Settings → Images, or add a GoAPI key")
            return

        safe_log(f"🖼️ Starting image generation (4 images: 1 featured + 3 body)...")
        names = ["featured","body-1","body-2","body-3"]
        img_threads = []

        def _gen_single(idx):
            slug = re.sub(r"[^a-z0-9]+","-",title.lower()).strip("-")
            fname = f"{slug}-{names[idx]}.webp"

            if idx == 0:
                target_ratio = (16, 9)
                poll_w, poll_h = 1280, 720
            else:
                target_ratio = (3, 2)
                poll_w, poll_h = 1024, 683

            if use_pollinations:
                tpl = pollinations_prompt or "Professional editorial photography of {title}, natural light, studio quality, 4K"
                ip = tpl.replace("{title}", title).replace("{recipe_name}", title)
                safe_log(f"  🖼️ Generating image {idx+1}/4 via Pollinations...")

                # Pass log_fn to pollinations for detailed logging
                res = generate_pollinations_image(ip, width=poll_w, height=poll_h, log_fn=safe_log)

                if not res.get("url") and not res.get("raw_bytes"):
                    safe_log(f"  ❌ Image {idx+1} failed: {res.get('error','unknown')}")
                    return

                raw = res.get("raw_bytes")

                # If we got a URL but no raw_bytes (shouldn't happen but safety net)
                if not raw and res.get("url"):
                    safe_log(f"  📥 Downloading image {idx+1} from URL...")
                    raw = download_image_bytes(res["url"], safe_log)

                if not raw:
                    safe_log(f"  ❌ Image {idx+1}: no image data")
                    return

                # Store raw bytes for Pinterest
                image_results[idx]["raw_bytes"] = raw

                # Convert to WebP
                safe_log(f"  🔄 Converting image {idx+1} to WebP...")
                webp = crop_and_convert_to_webp(raw, max_width=1920, target_ratio=target_ratio, log_fn=safe_log)

                if not webp:
                    safe_log(f"  ❌ Image {idx+1}: WebP conversion failed, using original URL")
                    if res.get("url"):
                        image_results[idx]["url"] = res["url"]
                    return

                # Upload to WordPress
                if wp_url and wp_password:
                    safe_log(f"  📤 Uploading image {idx+1} to WordPress...")
                    up = upload_image_to_wordpress(wp_url, wp_password, webp, fname, safe_log)
                    if up.get("success") and up.get("media_id"):
                        image_results[idx]["url"] = up["url"]
                        image_results[idx]["media_id"] = up["media_id"]
                        safe_log(f"  ✅ Image {idx+1} uploaded → media_id={up['media_id']}")
                        return
                    else:
                        safe_log(f"  ⚠️ Image {idx+1} WP upload failed: {up.get('error')} — using direct URL as fallback")
                        # Fallback: use the Pollinations URL directly
                        if res.get("url"):
                            image_results[idx]["url"] = res["url"]
                        return
                else:
                    safe_log(f"  ⚠️ No WP credentials — using Pollinations URL directly for image {idx+1}")
                    image_results[idx]["url"] = res.get("url","")

            elif goapi_key:
                tpl = mj_template or "Close up {recipe_name}, professional photography, natural light --ar 2:3"
                ip = tpl.replace("{recipe_name}", title).replace("{title}", title)
                if "--ar" not in ip: ip += " --ar 3:2"
                safe_log(f"  🖼️ Generating image {idx+1}/4 via Midjourney...")
                # generate_midjourney_image now downloads bytes immediately on completion
                res = generate_midjourney_image(goapi_key, ip, safe_log)

                if not res.get("url"):
                    safe_log(f"  ❌ MJ image {idx+1} failed: {res.get('error','unknown')}")
                    return

                # Use raw_bytes from MJ function (downloaded immediately, no 403)
                raw = res.get("raw_bytes")

                if not raw:
                    # Last resort: try downloading again (URL might still be valid)
                    safe_log(f"  📥 MJ image {idx+1}: retrying download...")
                    raw = download_image_bytes(res["url"], safe_log)

                if not raw:
                    safe_log(f"  ⚠️ MJ image {idx+1}: no bytes, using URL directly in article")
                    image_results[idx]["url"] = res["url"]
                    return

                image_results[idx]["raw_bytes"] = raw
                safe_log(f"  🔄 Converting MJ image {idx+1} to WebP...")
                webp = crop_and_convert_to_webp(raw, max_width=1920, target_ratio=target_ratio, log_fn=safe_log)

                if webp and wp_url and wp_password:
                    safe_log(f"  📤 Uploading MJ image {idx+1} to WordPress...")
                    up = upload_image_to_wordpress(wp_url, wp_password, webp, fname, safe_log)
                    if up.get("success") and up.get("media_id"):
                        image_results[idx]["url"] = up["url"]
                        image_results[idx]["media_id"] = up["media_id"]
                        safe_log(f"  ✅ MJ image {idx+1} uploaded to WP → media_id={up['media_id']}")
                        return
                    else:
                        safe_log(f"  ⚠️ MJ WP upload failed: {up.get('error')} — using direct MJ URL")
                        image_results[idx]["url"] = res["url"]
                else:
                    # No WP or webp failed — use MJ URL directly
                    image_results[idx]["url"] = res["url"]
                    if not webp:
                        safe_log(f"  ⚠️ WebP conversion failed for image {idx+1}, using original URL")

        for idx in range(4):
            t = threading.Thread(target=_gen_single, args=(idx,), daemon=True)
            img_threads.append(t)
            t.start()
        for t in img_threads:
            t.join(timeout=300)

        # Summary log
        for idx in range(4):
            r = image_results[idx]
            if r.get("media_id"):
                safe_log(f"  📸 Image {idx+1} ({names[idx]}): ✅ in WP media (id={r['media_id']})")
            elif r.get("url"):
                safe_log(f"  📸 Image {idx+1} ({names[idx]}): ✅ URL only (no WP upload)")
            else:
                safe_log(f"  📸 Image {idx+1} ({names[idx]}): ❌ not generated")

    # Launch article, card, images in parallel
    for fn in [_gen_article, _gen_card, _gen_images]:
        t = threading.Thread(target=fn, daemon=True)
        all_threads.append(t)
        t.start()

    deadline = time.time() + 600
    while any(t.is_alive() for t in all_threads):
        if time.time() > deadline:
            log("⚠️ Pipeline timeout after 10 minutes")
            break
        time.sleep(2)
    for t in all_threads:
        t.join(timeout=5)

    art = art_result[0]
    if not art or not art["success"]:
        return {"success":False,"error":art["error"] if art else "Article thread failed"}

    content = art["content"]

    # Inject images into article HTML
    content = inject_images_into_article(content, image_results, title, log_fn=log)

    # Append card
    if show_card and card_result[0]:
        content += "\n" + card_result[0]
        log("✅ Card appended to article")

    # Internal links
    _links = internal_links
    if use_internal_links and not _links and wp_url and wp_password:
        log("🔗 Fetching internal links from WordPress...")
        try:
            _links = fetch_internal_links(wp_url, wp_password, max_posts=200)
            log(f"🔗 Loaded {len(_links)} posts for internal linking")
        except Exception as e:
            log(f"⚠️ Internal links error: {e}")
    if _links and use_internal_links:
        mc = art.get("parsed",{}).get("MAIN","#ea580c")
        content = inject_internal_links(content, _links, title, max_links=max_links, main_color=mc)
        log("🔗 Internal links injected")

    meta = generate_meta_description(title)
    wp_title = art.get("seo_title") or title

    # Featured image
    featured_id = None
    featured_url = None
    r0 = image_results[0] if image_results else {}

    if r0.get("media_id"):
        try:
            featured_id = int(r0["media_id"])
            featured_url = r0.get("url","")
            log(f"🖼️ Featured image ready: media_id={featured_id}")
        except (ValueError, TypeError) as e:
            log(f"⚠️ Invalid media_id '{r0['media_id']}': {e}")
    elif r0.get("url"):
        featured_url = r0.get("url","")
        log(f"⚠️ Featured image has URL but NO media_id — will NOT be set as WP featured image")
        log(f"   Fix: check your WP App Password has media upload permission")
    else:
        if use_images:
            log("⚠️ No featured image was generated")

    log(f"📤 Publishing to WordPress (status={publish_status})...")
    pub = publish_to_wordpress(
        title=wp_title, content=content,
        wp_url=wp_url, wp_password=wp_password,
        status=publish_status, meta_description=meta,
        featured_media_id=featured_id,
        category_ids=category_ids,
    )

    if pub["success"]:
        log(f"🎉 Published! → {pub.get('post_url','')}")
        if featured_id:
            log(f"🖼️ Featured image set on post (media_id={featured_id})")
        else:
            log(f"ℹ️ No featured image set (images disabled or WP upload failed)")
        pub["featured_image_url"] = featured_url or ""
        pub["featured_media_id"] = featured_id
        pub["body_images_bytes"] = [image_results[i].get("raw_bytes") for i in range(1, 4)]
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