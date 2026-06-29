"""
主流程编排：抓取 → 生成 → 发布

用法:
    python src/main.py                    # 完整流程
    python src/main.py --skip-publish     # 只抓取和生成，不发布
    python src/main.py --fetch-only       # 只抓取
"""

import os
import sys
import json
import argparse
from datetime import datetime

# 将 src 目录加入 path
sys.path.insert(0, os.path.dirname(__file__))

from fetch_trending import fetch_trending
# Lazy imports for optional dependencies
# generate_article requires: pip install anthropic
# wechat_api requires: pip install requests (always available)


def main():
    parser = argparse.ArgumentParser(description="GitHub Trending → 微信日报")
    parser.add_argument("--skip-publish", action="store_true", help="只抓取和生成，不发布到微信")
    parser.add_argument("--fetch-only", action="store_true", help="只抓取 Trending 数据")
    parser.add_argument("--dry-run", action="store_true", help="使用 mock 数据，不调用真实 API")
    args = parser.parse_args()

    today_str = datetime.now().strftime("%Y%m%d")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    # ── Step 1: 抓取 ────────────────────────────────
    print("=" * 60)
    print("  STEP 1: Fetch GitHub Trending")
    print("=" * 60)

    if args.dry_run:
        repos = [
            {"rank": i, "full_name": f"owner/repo-{i}", "url": f"https://github.com/owner/repo-{i}",
             "language": "Python", "stars_today": 100 - i * 10,
             "description": f"An amazing open-source tool #{i}"}
            for i in range(1, 11)
        ]
        print("  [*] Using mock data (--dry-run)")
    else:
        repos_json = os.path.join(output_dir, f"trending_{today_str}.json")
        repos = fetch_trending(top_n=10, output_path=repos_json)

    if args.fetch_only:
        print("\n  Done. --fetch-only specified, exiting.")
        return

    # ── Step 2: AI 生成文章 ──────────────────────────
    print("")
    print("=" * 60)
    print("  STEP 2: Generate Article with Claude")
    print("=" * 60)

    from generate_article import generate_article

    article_path = os.path.join(output_dir, f"article_{today_str}.md")

    try:
        article = generate_article(repos=repos, output_path=article_path)
    except Exception as e:
        print(f"  [!] Article generation failed: {e}", file=sys.stderr)
        # 兜底：用简单模板生成一篇基础文章
        article = _fallback_article(repos)
        with open(article_path, "w", encoding="utf-8") as f:
            f.write(article)
        print(f"  [*] Used fallback template article")

    # ── Step 3: 发布到微信公众号 ─────────────────────
    print("")
    print("=" * 60)
    print("  STEP 3: Publish to WeChat")
    print("=" * 60)

    if args.skip_publish:
        print("  [*] --skip-publish specified, draft not created.")
    elif args.dry_run:
        print("  [*] --dry-run, skipping publish.")
    else:
        from wechat_api import publish_article

        try:
            # 提取标题（文章的第一行 # 标题）
            title = _extract_title(article)

            # 将 Markdown 转为简单的 HTML（微信草稿 API 支持）
            content_html = _md_to_wechat_html(article)

            result = publish_article(
                title=title,
                content=content_html,
                auto_publish=True,
            )
            print(f"\n  [+] Publish result: {json.dumps(result, ensure_ascii=False)}")
        except Exception as e:
            print(f"  [!] Publish failed: {e}", file=sys.stderr)
            print("  [*] Article saved to output/, please publish manually")

    print("")
    print("=" * 60)
    print("  DONE!")
    print(f"  Article: {article_path}")
    print("=" * 60)


def _extract_title(article: str) -> str:
    """从 Markdown 文章中提取标题"""
    today = datetime.now().strftime("%m月%d日")
    for line in article.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return f"GitHub 热榜日报 — {today}"


def _md_to_wechat_html(md_text: str) -> str:
    """将 Markdown 转为微信公众号兼容的 HTML"""
    # 简单转换（如果需要更丰富的格式，可接入 mistune 等库）
    lines = md_text.split("\n")
    html_lines = []
    in_paragraph = False

    for line in lines:
        line = line.strip()
        if not line:
            if in_paragraph:
                html_lines.append("</p>")
                in_paragraph = False
            continue

        if line.startswith("# "):
            if in_paragraph:
                html_lines.append("</p>")
                in_paragraph = False
            html_lines.append(f'<h1>{line[2:]}</h1>')
        elif line.startswith("## "):
            if in_paragraph:
                html_lines.append("</p>")
                in_paragraph = False
            html_lines.append(f'<h2>{line[3:]}</h2>')
        elif line == "---":
            if in_paragraph:
                html_lines.append("</p>")
                in_paragraph = False
            html_lines.append('<hr style="border:1px dashed #ddd;"/>')
        elif line.startswith("- "):
            if in_paragraph:
                html_lines.append("</p>")
                in_paragraph = False
            html_lines.append(f"<li>{line[2:]}</li>")
        else:
            if not in_paragraph:
                html_lines.append("<p>")
                in_paragraph = True
            else:
                html_lines.append("<br/>")
            # 简单加粗处理 **text**
            line = line.replace("**", "<b>", 1).replace("**", "</b>", 1)
            html_lines.append(line)

    if in_paragraph:
        html_lines.append("</p>")

    return "\n".join(html_lines)


def _fallback_article(repos: list[dict]) -> str:
    """当 AI 生成失败时，使用模板生成基础文章"""
    today = datetime.now().strftime("%Y年%m月%d日")
    lines = [
        f"# GitHub 热榜日报 — {today}",
        "",
        f"今天是 {today}，来看看 GitHub 上今天最热门的 10 个开源项目。",
        "",
    ]
    for r in repos:
        lines.append("---")
        lines.append(f"## {r['rank']}. [{r['full_name']}]({r['url']})")
        lines.append(f"⭐ 今日 +{r['stars_today']} stars  |  🔧 {r['language']}")
        lines.append(f"> {r['description']}")
        lines.append("")
    lines.append("---")
    lines.append("📬 **关注本号，每天上午 9 点获取 GitHub 热榜速递**")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
