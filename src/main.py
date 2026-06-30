"""
主流程编排：抓取 → 生成 → 构建网页

用法:
    python src/main.py                    # 完整流程
    python src/main.py --skip-build       # 只抓取和生成，不构建网页
    python src/main.py --fetch-only       # 只抓取
    python src/main.py --dry-run          # 使用 mock 数据
"""

import os
import sys
import json
import argparse
import io
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
# Fix encoding on Windows (GitHub Actions runner uses UTF-8 natively)
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except (AttributeError, ValueError):
    pass

from fetch_trending import fetch_trending


def main():
    parser = argparse.ArgumentParser(description="GitHub Trending → 网页热榜")
    parser.add_argument("--skip-build", action="store_true", help="只抓取和生成，不构建网页")
    parser.add_argument("--fetch-only", action="store_true", help="只抓取 Trending 数据")
    parser.add_argument("--dry-run", action="store_true", help="使用 mock 数据，不调用真实 API")
    args = parser.parse_args()

    today_str = datetime.now().strftime("%Y%m%d")
    project_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(project_dir, "output")
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
    print("  STEP 2: Generate Article with GitHub Models")
    print("=" * 60)

    from generate_article import generate_article

    article_path = os.path.join(output_dir, f"article_{today_str}.md")

    try:
        article = generate_article(repos=repos, output_path=article_path)
    except Exception as e:
        print(f"  [!] Article generation failed: {e}")
        article = _fallback_article(repos)
        with open(article_path, "w", encoding="utf-8") as f:
            f.write(article)
        print(f"  [*] Used fallback template article")

    # ── Step 3: 构建网页 ─────────────────────────────
    print("")
    print("=" * 60)
    print("  STEP 3: Build Web Page")
    print("=" * 60)

    if args.skip_build:
        print("  [*] --skip-build specified, skipping.")
    else:
        from build_page import build_daily_page

        index_path = build_daily_page(article, today_str, project_dir)

    print("")
    print("=" * 60)
    print("  DONE!")
    print(f"  Article: {article_path}")
    print(f"  Deploy:  Push to main → GitHub Pages auto-deploys")
    print("=" * 60)


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
    lines.append("📬 关注公众号，菜单点击「今日热榜」随时查看 🚀")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
