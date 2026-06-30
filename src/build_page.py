"""
将 AI 增强的 repo 数据 + Markdown 文章转为精美网页。
"""

import os
import re
from datetime import datetime, timezone

CSS = """
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    color: #c9d1d9;
    min-height: 100vh;
    padding: 20px;
  }
  .container { max-width: 760px; margin: 0 auto; }

  .hero {
    text-align: center;
    padding: 50px 20px 24px;
    border-bottom: 1px solid #21262d;
    margin-bottom: 20px;
  }
  .hero .badge {
    display: inline-block;
    background: #1f6feb33;
    color: #58a6ff;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    padding: 4px 14px;
    border-radius: 20px;
    margin-bottom: 12px;
  }
  .hero h1 { font-size: 1.75rem; color: #f0f6fc; margin-bottom: 6px; line-height: 1.3; }
  .hero .date { font-size: 0.85rem; color: #8b949e; margin-top: 4px; }
  .hero .tagline { font-size: 0.82rem; color: #8b949e; margin-top: 10px; line-height: 1.6; max-width: 520px; margin: 10px auto 0; }

  .stats {
    display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;
    margin: 24px 0 20px;
  }
  .stat-item { text-align: center; }
  .stat-item .num { font-size: 1.5rem; font-weight: 700; color: #e3b341; }
  .stat-item .label { font-size: 0.7rem; color: #8b949e; letter-spacing: .05em; margin-top: 2px; }

  .category-bar {
    display: flex; flex-wrap: wrap; justify-content: center; gap: 8px;
    margin: 0 0 30px;
  }
  .category-bar .ctag {
    font-size: 0.72rem; padding: 4px 12px; border-radius: 12px;
    background: #21262d; color: #8b949e; border: 1px solid #30363d;
  }

  .section-title {
    font-size: 0.95rem; color: #8b949e; margin: 30px 0 14px;
    padding-bottom: 8px; border-bottom: 1px solid #21262d;
  }

  .repo-card {
    background: #161b22; border: 1px solid #30363d; border-radius: 10px;
    padding: 22px 24px; margin-bottom: 16px;
    transition: border-color .2s, box-shadow .2s;
  }
  .repo-card:hover { border-color: #58a6ff; box-shadow: 0 0 0 1px #58a6ff22; }

  .repo-card .top-row {
    display: flex; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap;
  }
  .repo-card .rank {
    background: #21262d; color: #58a6ff; font-weight: 800; font-size: .75rem;
    width: 28px; height: 28px; border-radius: 7px;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .repo-card .rank.t1 { background: #e3b341; color: #0d1117; }
  .repo-card .rank.t2 { background: #adbac7; color: #0d1117; }
  .repo-card .rank.t3 { background: #cd8b62; color: #0d1117; }

  .repo-card .name {
    font-size: 1.05rem; font-weight: 600; color: #58a6ff; text-decoration: none; flex: 1;
  }
  .repo-card .name:hover { text-decoration: underline; }
  .repo-card .stars-badge {
    background: #21262d; border: 1px solid #30363d; border-radius: 6px;
    padding: 3px 12px; font-size: .8rem; color: #e3b341; font-weight: 600; flex-shrink: 0;
  }

  .repo-card .summary {
    font-size: .92rem; color: #f0f6fc; margin-bottom: 12px; line-height: 1.6;
  }

  .repo-card .highlights {
    list-style: none; margin: 10px 0 12px;
  }
  .repo-card .highlights li {
    font-size: .82rem; color: #c9d1d9; padding: 3px 0; line-height: 1.5;
  }
  .repo-card .highlights li::before { content: "▸ "; color: #58a6ff; }

  .repo-card .bottom-row {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
    margin-top: 12px; padding-top: 12px; border-top: 1px solid #21262d;
  }
  .repo-card .bottom-row .lang {
    font-size: .75rem; color: #8b949e;
  }
  .repo-card .bottom-row .suitable {
    font-size: .75rem; color: #8b949e; margin-left: auto;
  }
  .repo-card .bottom-row .suitable::before { content: "🎯 "; }

  .repo-card .tags { display: flex; gap: 5px; flex-wrap: wrap; }
  .repo-card .tags .tag {
    font-size: .68rem; padding: 2px 8px; border-radius: 8px;
    background: #1f6feb22; color: #58a6ff; border: 1px solid #1f6feb33;
  }

  .editor-pick {
    background: linear-gradient(135deg, #1a2332, #1a1f35);
    border: 1px solid #e3b34144; border-left: 3px solid #e3b341;
    border-radius: 10px; padding: 22px; margin: 28px 0 10px;
  }
  .editor-pick h3 { color: #e3b341; font-size: .9rem; margin-bottom: 10px; }
  .editor-pick p { font-size: .88rem; line-height: 1.75; color: #c9d1d9; }

  .footer {
    text-align: center; padding: 40px 20px 30px; color: #484f58;
    font-size: .8rem; line-height: 2;
  }
  .footer a { color: #58a6ff; text-decoration: none; }
  .footer a:hover { text-decoration: underline; }
  .footer .cta { color: #c9d1d9; font-size: .9rem; margin-bottom: 12px; }

  @media (max-width: 500px) {
    .hero h1 { font-size: 1.25rem; }
    .repo-card { padding: 14px 16px; }
    .stats { gap: 16px; }
    .stat-item .num { font-size: 1.2rem; }
  }
"""

ARCHIVE_CSS = """
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:#0d1117; color:#c9d1d9; min-height:100vh; padding:20px; }
  .container { max-width:600px; margin:0 auto; }
  h1 { color:#58a6ff; text-align:center; margin:30px 0 20px; }
  a { color:#58a6ff; text-decoration:none; }
  a:hover { text-decoration:underline; }
  .archive-item { display:flex; justify-content:space-between; align-items:center; padding:14px 18px; border-bottom:1px solid #21262d; transition:background .15s; }
  .archive-item:hover { background:#161b22; }
  .archive-item a { font-size:.95rem; }
  .archive-item .date { font-size:.8rem; color:#8b949e; }
  .back { text-align:center; margin:30px; }
"""


def build_daily_page(
    article_md: str,
    repo_details: list[dict],
    repos_raw: list[dict],
    today_str: str,
    output_dir: str,
) -> str:
    """构建今日热榜首页"""
    today_fmt = datetime.strptime(today_str, "%Y%m%d").strftime("%Y 年 %m 月 %d 日")

    # Title from article
    title = "GitHub 热榜日报"
    for line in article_md.split("\n"):
        if line.strip().startswith("# "):
            title = line.strip()[2:]
            break

    # Stats
    total_stars = sum(r.get("stars_today", 0) or 0 for r in repos_raw)
    cats = {}
    for d in repo_details:
        for c in d.get("category", "其他").split(","):
            c = c.strip()
            if c: cats[c] = cats.get(c, 0) + 1
    top_cats = sorted(cats, key=cats.get, reverse=True)[:5]

    stats_html = f"""
    <div class="stats">
      <div class="stat-item"><div class="num">{len(repos_raw)}</div><div class="label">上榜项目</div></div>
      <div class="stat-item"><div class="num">{total_stars:,}</div><div class="label">今日总 Star</div></div>
      <div class="stat-item"><div class="num">{len(cats)}</div><div class="label">涉及领域</div></div>
    </div>"""

    cat_html = '<div class="category-bar">' + ''.join(
        f'<span class="ctag">{c}</span>' for c in top_cats
    ) + '</div>'

    # Repo cards
    cards = ""
    for i, d in enumerate(repo_details):
        rank = d.get("rank", i + 1)
        rc = ""
        if rank == 1: rc = "t1"
        elif rank == 2: rc = "t2"
        elif rank == 3: rc = "t3"

        raw = repos_raw[i] if i < len(repos_raw) else {}
        name = raw.get("full_name", "unknown/repo")
        url = raw.get("url", "#")
        stars = raw.get("stars_today", 0) or 0
        lang = raw.get("language", "")

        summary = d.get("cn_summary", "")
        highlights = d.get("highlights", [])
        suitable = d.get("suitable_for", "")
        category = d.get("category", "")

        hl_html = "".join(f"<li>{h}</li>" for h in highlights[:3]) if highlights else ""
        tags_html = "".join(
            f'<span class="tag">{t.strip()}</span>'
            for t in category.split(",") if t.strip()
        ) if category else ""
        lang_html = f'<span class="lang">🔧 {lang}</span>' if lang else ""
        suit_html = f'<span class="suitable">{suitable}</span>' if suitable else ""

        cards += f"""
    <div class="repo-card">
      <div class="top-row">
        <div class="rank {rc}">{rank}</div>
        <a class="name" href="{url}" target="_blank">{name}</a>
        <span class="stars-badge">⭐ {stars:,}</span>
      </div>
      <div class="summary">{summary}</div>
      {('<ul class="highlights">' + hl_html + '</ul>') if hl_html else ''}
      <div class="bottom-row">
        {lang_html}
        <div class="tags">{tags_html}</div>
        {suit_html}
      </div>
    </div>"""

    # Editor's pick = #1 project
    # Try to extract editor pick text from article
    pick_html = ""
    pick_match = re.search(r'今日之星[^\n]*\n(.*?)(?:\n---|\n#|\Z)', article_md, re.DOTALL)
    if pick_match:
        pick_text = pick_match.group(1).strip()[:300]
        pick_html = f"""<div class="editor-pick">
      <h3>⭐ 今日之星</h3>
      <p>{pick_text}</p>
    </div>"""

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="GitHub Trending 每日热榜 - AI 自动整理 Top 10 开源项目">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">

  <div class="hero">
    <div class="badge">Daily Trending</div>
    <h1>{title}</h1>
    <div class="date">{today_fmt} · 每天 9:00 自动更新</div>
    <div class="tagline">AI 自动抓取 GitHub Trending Top 10，逐个项目提炼亮点、领域标签和适用场景，三分钟看完今日开源动态。</div>
  </div>

  {stats_html}
  {cat_html}

  <div class="section-title">📋 今日 Top {len(repos_raw)}</div>

  {cards}

  {pick_html}

  <div class="footer">
    <div class="cta">📬 关注公众号 <strong>星探日报</strong>，底部菜单「今日热榜」随时查看</div>
    <p>Powered by <a href="https://github.com/MRJI55/github-trending-wechat">GitHub Actions</a> · AI by <a href="https://github.com/marketplace/models">GitHub Models (Llama 3.3)</a> · Hosted on <a href="https://pages.github.com">GitHub Pages</a></p>
    <p><a href="./archive/">📁 历史归档</a> · <a href="https://github.com/MRJI55/github-trending-wechat">⭐ Star on GitHub</a></p>
    <p style="font-size:.7rem;margin-top:8px;">最后更新：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC</p>
  </div>

</div>
</body>
</html>"""

    docs_dir = os.path.join(output_dir, "docs")
    archive_dir = os.path.join(docs_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)

    index_path = os.path.join(docs_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(page)

    # Archive copy
    archive_path = os.path.join(archive_dir, f"{today_str}.html")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(page)

    _update_archive_index(archive_dir)

    print(f"  [+] Page saved: {index_path}")
    print(f"  [+] Archive: {archive_path}")
    return index_path


def _update_archive_index(archive_dir: str):
    files = sorted(
        [f for f in os.listdir(archive_dir) if f.endswith(".html") and f != "index.html"],
        reverse=True,
    )
    items = ""
    for f in files:
        ds = f.replace(".html", "")
        try:
            label = datetime.strptime(ds, "%Y%m%d").strftime("%m 月 %d 日")
        except ValueError:
            label = ds
        items += f'<div class="archive-item"><a href="{f}">{label} 热榜日报</a><span class="date">{ds}</span></div>\n'

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>历史归档 - GitHub 热榜日报</title>
<style>{ARCHIVE_CSS}</style>
</head>
<body>
<div class="container">
  <h1>📁 历史归档</h1>
  {items}
  <div class="back"><a href="../">&larr; 返回今日热榜</a></div>
</div>
</body>
</html>"""
    with open(os.path.join(archive_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)


if __name__ == "__main__":
    test_details = [
        {"rank": 1, "cn_summary": "拖拽式构建LLM工作流的低代码平台",
         "highlights": ["支持100+模型接入", "可视化RAG管道", "一键部署为API"],
         "suitable_for": "想快速搭建AI应用的独立开发者",
         "category": "AI Agent, 自动化"},
        {"rank": 2, "cn_summary": "Rust重写的下一代终端文件管理器",
         "highlights": ["比传统方案快5倍", "支持多窗口和语法高亮", "原生Git集成"],
         "suitable_for": "Rust爱好者和命令行重度用户",
         "category": "命令行工具, 开源替代品"},
        {"rank": 3, "cn_summary": "Anthropic官方AI开发教程合集",
         "highlights": ["覆盖Prompt Engineering", "完整可运行Notebook", "Tool Use实战"],
         "suitable_for": "想系统学习AI开发的程序员",
         "category": "AI/大模型, 文档/知识库"},
    ]
    test_raw = [
        {"rank": 1, "full_name": "langflow-ai/langflow", "url": "https://github.com/langflow-ai/langflow",
         "language": "Python", "stars_today": 3000, "description": "Low-code AI builder"},
        {"rank": 2, "full_name": "rustic-rs/rustic", "url": "https://github.com/rustic-rs/rustic",
         "language": "Rust", "stars_today": 1800, "description": "Terminal file manager"},
        {"rank": 3, "full_name": "anthropics/courses", "url": "https://github.com/anthropics/courses",
         "language": "Jupyter Notebook", "stars_today": 1500, "description": "AI tutorials"},
    ]
    build_daily_page("# Test Title\n\nIntro paragraph here.", test_details, test_raw, "20260630",
                     os.path.dirname(os.path.dirname(__file__)))
    print("Test page built!")
