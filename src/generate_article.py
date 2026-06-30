"""
调用 GitHub Models API 生成增强文章。

输出: (repo_details, article_markdown)
- repo_details: 每个项目的结构化数据（亮点、标签、适用人群）
- article_markdown: 完整 Markdown 文章
"""

import os
import json
import re
import sys
from datetime import datetime
from typing import Optional, Tuple
from openai import OpenAI

GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"
DEFAULT_MODEL = "Llama-3.3-70B-Instruct"


def load_prompt_template() -> str:
    base_dirs = [
        os.path.dirname(os.path.dirname(__file__)),
        os.path.dirname(__file__),
        os.getcwd(),
    ]
    for base in base_dirs:
        prompt_path = os.path.join(base, "templates", "prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
    return _default_prompt()


def _default_prompt() -> str:
    return """你是一位资深科技编辑。为每个 GitHub Trending 项目提供增强信息和文章。

输出格式：先输出 JSON，再用 ===ARTICLE=== 分隔，然后输出文章。

```json
{"repos":[{"rank":1,"cn_summary":"...","highlights":["...","...","..."],"suitable_for":"...","category":"..."}]}
```

===ARTICLE===

# 今日标题
..."""


def generate_article(
    repos: list[dict],
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    output_path: Optional[str] = None,
) -> Tuple[list[dict], str]:
    """
    Returns:
        (repo_details, article_markdown)
        - repo_details: enriched per-repo structured data
        - article_markdown: full markdown article
    """
    api_key = api_key or os.environ.get("GITHUB_TOKEN")
    if not api_key:
        raise ValueError("GITHUB_TOKEN not set.")

    repos_text = _format_repos_for_prompt(repos)
    today = datetime.now().strftime("%Y年%m月%d日")
    system_prompt = load_prompt_template()

    user_message = f"""今天是 {today}，以下是 GitHub Trending 今日 Top 10 项目数据：

{repos_text}

请为每个项目生成增强信息（JSON）和完整文章（===ARTICLE=== 之后）。"""

    print(f"[{datetime.now().isoformat()}] Calling GitHub Models ({model})...")

    client = OpenAI(base_url=GITHUB_MODELS_ENDPOINT, api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        max_tokens=3500,
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    raw = response.choices[0].message.content
    usage = response.usage

    print(f"  [+] Response: {len(raw)} chars")
    print(f"  [+] Token usage: input={usage.prompt_tokens}, output={usage.completion_tokens}")

    # Parse JSON + Article
    repo_details, article = _parse_response(raw, repos)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(article)
        print(f"  [+] Article saved to {output_path}")

    return repo_details, article


def _parse_response(raw: str, repos: list[dict]) -> Tuple[list[dict], str]:
    """从 AI 原始响应中分离 JSON 和文章"""
    repo_details = []
    article = raw

    # Try to extract JSON block
    json_match = re.search(r'```json\s*\n(.*?)\n```', raw, re.DOTALL)
    if not json_match:
        json_match = re.search(r'\{[\s\S]*"repos"[\s\S]*?\n\}', raw)
    if not json_match:
        # Try to find just a JSON object
        json_match = re.search(r'\{[\s\S]*?"rank"[\s\S]*?"category"[\s\S]*?\}', raw)

    if json_match:
        json_str = json_match.group(1) if json_match.lastindex else json_match.group(0)
        # Clean up trailing commas before ] or }
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        try:
            data = json.loads(json_str)
            if "repos" in data:
                repo_details = data["repos"]
                print(f"  [+] Parsed {len(repo_details)} enhanced repos from JSON")
        except json.JSONDecodeError as e:
            print(f"  [!] JSON parse failed: {e}, using fallback")

    # Extract article (everything after ===ARTICLE===)
    article_match = re.split(r'===ARTICLE===', raw, maxsplit=1)
    if len(article_match) > 1:
        article = article_match[1].strip()

    # Fallback: enrich repos with basic info if AI didn't provide enough
    if len(repo_details) < len(repos):
        print(f"  [*] Enriching {len(repos) - len(repo_details)} repos with fallback data")
        for i, r in enumerate(repos):
            if i >= len(repo_details):
                repo_details.append({
                    "rank": r["rank"],
                    "cn_summary": r.get("description", "")[:50],
                    "highlights": [r.get("description", "")[:30]],
                    "suitable_for": "开发者",
                    "category": r.get("language", "其他"),
                })

    return repo_details, article


def _format_repos_for_prompt(repos: list[dict]) -> str:
    lines = []
    for r in repos:
        lines.append(f"#{r['rank']} {r['full_name']}")
        lines.append(f"  链接: {r['url']}")
        lines.append(f"  语言: {r['language']}")
        lines.append(f"  今日Star: {r['stars_today']}")
        lines.append(f"  简介: {r['description']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    mock = [
        {"rank": i, "full_name": f"owner/repo-{i}", "url": f"https://github.com/owner/repo-{i}",
         "language": "Python", "stars_today": 100 - i * 10,
         "description": f"Amazing tool #{i}"}
        for i in range(1, 11)
    ]
    details, art = generate_article(mock)
    print("\n=== Enriched Repos ===")
    for d in details[:3]:
        print(f"  #{d['rank']} {d['cn_summary']} | tags={d.get('category','')} | {d['highlights'][:2]}")
    print("\n=== Article Preview ===")
    print(art[:400])
