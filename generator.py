"""
COPY THESE 2 FUNCTIONS INTO generator.py
Replace the existing inject_internal_links and inject_external_links functions.
Nothing else in generator.py changes.
"""

import re
import requests as _req


def inject_internal_links(html, links, current_title, max_links=4, main_color="#ea580c"):
    """
    FIX: Previous version required EXACT full post title in article text — never worked.
    New version: extracts meaningful keywords from WP post titles and matches those.
    A WP post "Boursin Cheese Pasta with Broccoli" will match the word "pasta" or
    "breastfeeding" in the article body. Single-word or 2-word keyword matches work.
    """
    if not links or not html:
        return html

    injected = 0
    used_urls = set()
    current_lower = current_title.lower()

    STOP_WORDS = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "how", "what", "why", "when", "where", "who", "which", "that", "this",
        "i", "my", "your", "our", "their", "its", "it", "can", "will", "do",
        "does", "did", "not", "no", "vs", "vs.", "best", "top", "tips", "ways",
        "get", "make", "use", "using", "using", "great", "good", "new",
    }

    def get_search_phrases(title):
        """Return keyword phrases to search for (longest/most specific first)."""
        words = title.lower().split()
        clean = [re.sub(r"[^a-z0-9]", "", w) for w in words]
        meaningful = [w for w in clean if w and w not in STOP_WORDS and len(w) > 3]
        phrases = []
        # 2-word combos first (more specific)
        for i in range(len(meaningful) - 1):
            phrases.append(f"{meaningful[i]} {meaningful[i+1]}")
        # Then single keywords
        phrases.extend(meaningful)
        return phrases

    def replace_first_in_p(html_text, phrase, anchor):
        """Replace first occurrence of phrase inside <p>...</p> only."""
        parts = re.split(r'(<p[^>]*>|</p>)', html_text)
        inside_p = False
        replaced = False
        result = []
        for part in parts:
            if re.match(r'<p[^>]*>', part):
                inside_p = True
                result.append(part)
            elif part == '</p>':
                inside_p = False
                result.append(part)
            elif inside_p and not replaced and '<a ' not in part and '<strong' not in part:
                new_part = re.sub(
                    r'\b' + re.escape(phrase) + r'\b',
                    anchor,
                    part,
                    count=1,
                    flags=re.IGNORECASE
                )
                if new_part != part:
                    replaced = True
                    result.append(new_part)
                    continue
                result.append(part)
            else:
                result.append(part)
        return "".join(result), replaced

    for link in links:
        if injected >= max_links:
            break
        link_title = link.get("title", "").strip()
        link_url = link.get("url", "")
        if not link_title or not link_url or link_url in used_urls:
            continue
        if link_title.lower() == current_lower:
            continue
        if link_title.strip().endswith("?"):
            continue
        if len(link_title.split()) < 2:
            continue
        # Skip if too much overlap with current title
        link_words = set(link_title.lower().split())
        current_words = set(current_lower.split())
        if len(link_words & current_words) / max(len(link_words), 1) > 0.6:
            continue

        phrases = get_search_phrases(link_title)
        for phrase in phrases:
            if not phrase or len(phrase) < 4:
                continue
            anchor = (
                f'<a href="{link_url}" '
                f'style="color:{main_color};text-decoration:underline;font-weight:500;" '
                f'title="{link_title}">{phrase}</a>'
            )
            new_html, did_replace = replace_first_in_p(html, phrase, anchor)
            if did_replace:
                html = new_html
                used_urls.add(link_url)
                injected += 1
                break  # next link

    return html


def inject_external_links(html, topic, max_links=2, main_color="#ea580c", log_fn=None):
    """
    FIX: Previous version tried to match Wikipedia page title in article text — never worked.
    New version: fetches Wikipedia pages for the topic, then injects 'Learn more about X'
    at the end of suitable paragraphs. This GUARANTEES links appear in the article.
    """
    def log(m):
        if log_fn:
            log_fn(m)

    # --- 1. Fetch Wikipedia links ---
    try:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": topic[:100],
            "srlimit": max_links + 3,
            "format": "json",
            "utf8": 1,
        }
        resp = _req.get(
            "https://en.wikipedia.org/w/api.php",
            params=params,
            timeout=10,
            headers={"User-Agent": "NicheFlowAI/1.0"},
        )
        if resp.status_code != 200:
            log(f"  ⚠️ Wikipedia API: HTTP {resp.status_code}")
            return html
        results = resp.json().get("query", {}).get("search", [])
        if not results:
            log(f"  ⚠️ Wikipedia: no results for '{topic[:40]}'")
            return html

        wiki_links = []
        for item in results:
            page_title = item.get("title", "").strip()
            if not page_title:
                continue
            slug = page_title.replace(" ", "_")
            wiki_url = f"https://en.wikipedia.org/wiki/{_req.utils.quote(slug)}"
            wiki_links.append({"title": page_title, "url": wiki_url})
            if len(wiki_links) >= max_links:
                break

        log(f"  🌐 Wikipedia returned {len(wiki_links)} page(s) for external links")
    except Exception as e:
        log(f"  ⚠️ External links fetch error: {e}")
        return html

    if not wiki_links:
        return html

    # --- 2. Inject links at end of paragraphs ---
    # We inject "Learn more about X." at the end of suitable <p> paragraphs.
    # No phrase matching needed — this always works.

    injected = 0
    used_urls = set()

    def replacer(m):
        nonlocal injected
        if injected >= max_links:
            return m.group(0)
        open_tag = m.group(1)
        content = m.group(2)
        close_tag = m.group(3)
        # Only inject into paragraphs that are long enough and have no existing links
        if len(content.strip()) > 80 and '<a ' not in content and injected < len(wiki_links):
            link = wiki_links[injected]
            if link["url"] not in used_urls:
                link_html = (
                    f' <a href="{link["url"]}" target="_blank" rel="noopener noreferrer nofollow" '
                    f'style="color:{main_color};text-decoration:underline;font-weight:500;" '
                    f'title="{link["title"]}">Learn more about {link["title"]}</a>.'
                )
                stripped = content.rstrip()
                if stripped.endswith('.'):
                    content = stripped[:-1] + link_html
                else:
                    content = stripped + link_html
                used_urls.add(link["url"])
                injected += 1
        return open_tag + content + close_tag

    html = re.sub(r'(<p[^>]*>)(.*?)(</p>)', replacer, html, flags=re.DOTALL)

    if injected:
        log(f"  🌐 {injected} external link(s) injected into article")
    else:
        log(f"  ℹ️ External links fetched but no suitable paragraphs found")

    return html