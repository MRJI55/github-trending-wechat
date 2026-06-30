"""
将生成的 Markdown 文章转为精美网页，部署到 GitHub Pages。

输出:
  docs/index.html          — 今日热榜（首页）
  docs/archive/20260630.html  — 历史归档
"""

import os
import re
import json
import shutil
from datetime import datetime


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    color: #c9d1d9;
    min-height: 100vh;
    padding: 20px;
  }}
  .container {{
    max-width: 700px;
    margin: 0 auto;
  }}
  .header {{
    text-align: center;
    padding: 40px 20px 20px;
  }}
  .header h1 {{
    font-size: 1.6rem;
    color: #58a6ff;
    margin-bottom: 6px;
  }}
  .header .date {{
    font-size: 0.85rem;
    color: #8b949e;
  }}
  .header .subtitle {{
    font-size: 0.9rem;
    color: #8b949e;
    margin-top: 8px;
    line-height: 1.6;
  }}
  .intro {{
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 20px;
    font-size: 0.9rem;
    line-height: 1.7;
    color: #c9d1d9;
  }}
  .repo-card {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 14px;
    transition: border-color 0.2s;
  }}
  .repo-card:hover {{ border-color: #58a6ff; }}
  .repo-card .rank {{
    display: inline-block;
    background: #21262d;
    color: #58a6ff;
    font-weight: 700;
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 10px;
    margin-right: 8px;
    vertical-align: middle;
  }}
  .repo-card .name {{
    font-size: 1.05rem;
    font-weight: 600;
    color: #58a6ff;
    text-decoration: none;
    vertical-align: middle;
  }}
  .repo-card .name:hover {{ text-decoration: underline; }}
  .repo-card .meta {{
    margin-top: 8px;
    font-size: 0.8rem;
    color: #8b949e;
  }}
  .repo-card .meta span {{
    margin-right: 12px;
  }}
  .repo-card .meta .stars {{ color: #e3b341; }}
  .repo-card .meta .lang {{ color: #8b949e; }}
  .repo-card .desc {{
    margin-top: 8px;
    font-size: 0.88rem;
    line-height: 1.6;
    color: #c9d1d9;
  }}
  .repo-card .suitable {{
    margin-top: 6px;
    font-size: 0.8rem;
    color: #8b949e;
    font-style: italic;
  }}
  .footer {{
    text-align: center;
    padding: 30px 20px;
    color: #484f58;
    font-size: 0.8rem;
    line-height: 1.8;
  }}
  .footer a {{
    color: #58a6ff;
    text-decoration: none;
  }}
  .footer a:hover {{ text-decoration: underline; }}
  .divider {{
    border: none;
    border-top: 1px solid #21262d;
    margin: 12px 0;
  }}
  .archive-link {{
    display: block;
    text-align: center;
    margin: 20px 0;
    color: #58a6ff;
    font-size: 0.85rem;
  }}
  .star-btn {{
    display: inline-block;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.75rem;
    color: #c9d1d9;
    text-decoration: none;
    margin-left: 8px;
    vertical-align: middle;
  }}
  .star-btn:hover {{ background: #30363d; color: #e3b341; }}
  @media (max-width: 500px) {{
    .header h1 {{ font-size: 1.3rem; }}
    .repo-card {{ padding: 14px 16px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🔥 GitHub 热榜日报</h1>
    <div class="date">{date_display}</div>
    <div class="subtitle">每天上午 9:00 自动更新 &middot; AI 整理 Top 10</div>
  </div>
  {intro_html}
  {cards_html}
  <hr class="divider">
  <div class="footer">
    <p>📬 关注公众号 <strong>星探日报</strong>，菜单点击「今日热榜」随时查看</p>
    <p>Powered by <a href="https://github.com/MRJI55/github-trending-wechat">GitHub Actions</a> &middot; AI by GitHub Models</p>
    <p><a href="./archive/">📁 历史归档</a></p>
  </div>
</div>
</body>
</html>"""


ARCHIVE_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>历史归档 - GitHub 热榜日报</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    min-height: 100vh;
    padding: 20px;
  }}
  .container {{ max-width: 600px; margin: 0 auto; }}
  h1 {{ color: #58a6ff; text-align: center; margin: 30px 0 20px; }}
  a {{ color: #58a6ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .archive-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid #21262d;
  }}
  .archive-item .link {{ font-size: 0.95rem; }}
  .archive-item .date {{ font-size: 0.8rem; color: #8b949e; }}
  .back {{ text-align: center; margin: 20px; }}
</style>
</head>
<body>
<div class="container">
  <h1>📁 历史归档</h1>
  {archive_items}
  <div class="back"><a href="../">← 返回今日热榜</a></div>
</div>
</body>
</html>"""


ARTICLE_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    min-height: 100vh;
    padding: 20px;
  }}
  .container {{ max-width: 700px; margin: 0 auto; }}
  .back {{ text-align: center; margin: 10px 0 20px; }}
  .back a {{ color: #58a6ff; text-decoration: none; font-size: 0.85rem; }}
  .back a:hover {{ text-decoration: underline; }}
  {extra_css}
</style>
</head>
<body>
<div class="container">
  <div class="back"><a href="../../">← 返回热榜</a> | <a href="../">← 归档</a></div>
  {body_html}
</div>
</body>
</html>"""


def md_to_html(md_text: str) -> str:
    """极简 Markdown → HTML 转换"""
    lines = md_text.split("\n")
    html = []
    in_p = False
    in_list = False

    def close_para():
        nonlocal in_p, in_list
        if in_p:
            html.append("</p>")
            in_p = False
        if in_list:
            html.append("</ul>")
            in_list = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            close_para()
            continue

        if stripped.startswith("# "):
            close_para()
            html.append(f'<h1 style="color:#58a6ff;margin:20px 0 10px;font-size:1.4rem;">{stripped[2:]}</h1>')
        elif stripped.startswith("## "):
            close_para()
            html.append(f'<h2 style="color:#e6edf3;margin:16px 0 8px;font-size:1.1rem;">{stripped[3:]}</h2>')
        elif stripped == "---":
            close_para()
            html.append('<hr style="border:none;border-top:1px solid #30363d;margin:16px 0;">')
        elif stripped.startswith("- "):
            if not in_list:
                html.append('<ul style="padding-left:20px;">')
                in_list = True
            html.append(f"<li>{_inline_format(stripped[2:])}</li>")
        else:
            if not in_p:
                html.append('<p style="line-height:1.8;margin:8px 0;">')
                in_p = True
            else:
                html.append("<br>")
            html.append(_inline_format(stripped))

    close_para()
    return "\n".join(html)


def _inline_format(text: str) -> str:
    """处理行内格式：**加粗**、链接"""
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Links: [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" style="color:#58a6ff;">\1</a>', text)
    # Emoji preservation
    return text


def build_daily_page(article_md: str, today_str: str, output_dir: str) -> str:
    """
    将 Markdown 文章转成美观网页。

    Returns: 生成的 index.html 路径
    """
    # Extract title and intro
    lines = article_md.split("\n")
    title = "GitHub 热榜日报"
    intro_parts = []
    cards_html = ""
    in_intro = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:]
            continue
        if stripped == "---":
            in_intro = False
            continue
        # Everything before first --- is intro
        if not cards_html and not stripped.startswith("## ") and not stripped.startswith("- ") and stripped:
            intro_parts.append(stripped)

    # Build intro HTML
    intro_html = ""
    if intro_parts:
        intro_text = " ".join(intro_parts)[:300]
        intro_html = f'<div class="intro">📊 {intro_text}</div>'

    # Build cards from the full Markdown body
    body_html = md_to_html(article_md)
    # Remove the title and intro from body (they're already in header/intro)
    # Simple approach: just put full body after intro
    # Actually, let's strip h1 from body
    body_html = re.sub(r'<h1[^>]*>.*?</h1>', '', body_html, count=1)

    today_fmt = datetime.strptime(today_str, "%Y%m%d").strftime("%Y 年 %m 月 %d 日")

    page = HTML_TEMPLATE.format(
        title=title,
        date_display=today_fmt,
        intro_html=intro_html,
        cards_html=body_html,
    )

    # Ensure output dirs
    docs_dir = os.path.join(output_dir, "docs")
    archive_dir = os.path.join(docs_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)

    # Write today's page as index.html
    index_path = os.path.join(docs_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(page.encode("ascii", "xmlcharrefreplace").decode("ascii")
                if all(ord(c) < 128 for c in page) else page)

    # Also save to archive
    archive_path = os.path.join(archive_dir, f"{today_str}.html")
    archive_page = build_archive_article(article_md, today_str)
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(archive_page)

    # Update archive index
    _update_archive_index(archive_dir)

    print(f"  [+] Page saved: {index_path}")
    print(f"  [+] Archive: {archive_path}")
    return index_path


def build_archive_article(article_md: str, date_str: str) -> str:
    """构建归档文章页"""
    body = md_to_html(article_md)
    title = "GitHub 热榜日报"
    for line in article_md.split("\n"):
        if line.strip().startswith("# "):
            title = line.strip()[2:]
            break

    return ARTICLE_PAGE_TEMPLATE.format(
        title=title,
        extra_css="",
        body_html=body,
    )


def _update_archive_index(archive_dir: str):
    """更新归档首页"""
    files = sorted(
        [f for f in os.listdir(archive_dir) if f.endswith(".html") and f != "index.html"],
        reverse=True,
    )

    items = ""
    for f in files:
        date_str = f.replace(".html", "")
        try:
            dt = datetime.strptime(date_str, "%Y%m%d")
            label = dt.strftime("%m 月 %d 日")
        except ValueError:
            label = date_str
        items += f'<div class="archive-item"><a class="link" href="{f}">{label} 热榜</a><span class="date">{date_str}</span></div>\n'

    page = ARCHIVE_INDEX_TEMPLATE.format(archive_items=items)

    idx_path = os.path.join(archive_dir, "index.html")
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(page)


if __name__ == "__main__":
    test_md = """# 6月30日热榜 | AI 工具今天又炸了

今天的热榜非常有意思，AI Agent 类项目占据了半壁江山。

---

## 1. [example/awesome-project](https://github.com/example/awesome-project)
⭐ 今日 +2000 stars | 🔧 Python
> 一个超级好用的 AI Agent 框架

🎯 适合：AI 开发者

---

📬 关注公众号，每天早上 9 点获取热榜速递 🚀"""

    build_daily_page(test_md, "20260630", os.path.dirname(os.path.dirname(__file__)))
    print("Test page built!")
