"""
调用 GitHub Models API（免费）生成微信公众号文章。

GitHub Models: https://github.com/marketplace/models
兼容 OpenAI SDK，使用 GitHub Token 鉴权，完全免费。
"""

import os
import json
import sys
from datetime import datetime
from typing import Optional
from openai import OpenAI

# GitHub Models 免费端点
GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"

# 免费模型（按中文能力排序推荐）
# Llama-3.3-70B-Instruct: Meta 旗舰，中文优秀
# Mistral-Large: 欧洲最强，多语言出色
# Phi-4: 微软出品，轻量快速
DEFAULT_MODEL = "Llama-3.3-70B-Instruct"


def load_prompt_template() -> str:
    """从 templates/prompt.md 读取 system prompt"""
    base_dirs = [
        os.path.dirname(os.path.dirname(__file__)),  # src/ 的上级
        os.path.dirname(__file__),                   # src/
        os.getcwd(),                                  # 当前工作目录
    ]
    for base in base_dirs:
        prompt_path = os.path.join(base, "templates", "prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()

    return _default_prompt()


def _default_prompt() -> str:
    return """你是一位资深的科技编辑，负责撰写「GitHub 热榜日报」微信公众号文章。

你的任务是：根据给定的 GitHub Trending Top 10 数据，撰写一篇结构清晰、易读的文章。

## 格式要求

1. **标题**：吸引眼球，包含当天日期，字数不超过20字
2. **导语**（2-3句）：概述今天的整体趋势和亮点
3. **正文**：每个项目一个卡片式摘要，包含：
   - 项目名称 + 链接
   - ⭐ 今日新增 Star 数
   - 一句话简介（用通俗语言解释它是干什么的）
   - 🔖 适用人群 / 使用场景
4. **结尾**：一句话引导关注

## 排版要求

- 使用公众号常用的排版格式
- 每个项目之间用分割线隔开
- 重要信息用加粗或 emoji 突出
- 全文 800-1500 字

## 输出格式

直接输出文章内容（Markdown 格式），不要包含额外的说明文字。"""


def generate_article(
    repos: list[dict],
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    output_path: Optional[str] = None,
) -> str:
    """
    调用 GitHub Models API 生成公众号文章。

    Args:
        repos: 从 fetch_trending 获取的项目列表
        api_key: GitHub Token（默认从 GITHUB_TOKEN 环境变量读取）
        model: 使用的模型 ID（免费模型列表见 DEFAULT_MODEL 上方注释）
        output_path: 保存文章的路径（可选）

    Returns:
        str: 生成的文章内容 (Markdown)
    """
    api_key = api_key or os.environ.get("GITHUB_TOKEN")
    if not api_key:
        raise ValueError(
            "GITHUB_TOKEN not set. Set environment variable or pass api_key parameter.\n"
            "Get your token: https://github.com/settings/tokens"
        )

    repos_text = _format_repos_for_prompt(repos)
    today = datetime.now().strftime("%Y年%m月%d日")
    system_prompt = load_prompt_template()

    user_message = f"""今天是 {today}，以下是 GitHub Trending 今日 Top 10 项目数据：

{repos_text}

请根据以上数据，撰写今日的 GitHub 热榜日报。"""

    print(f"[{datetime.now().isoformat()}] Calling GitHub Models ({model})...")

    client = OpenAI(
        base_url=GITHUB_MODELS_ENDPOINT,
        api_key=api_key,
    )

    response = client.chat.completions.create(
        model=model,
        max_tokens=3000,
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    article = response.choices[0].message.content
    usage = response.usage

    print(f"  [+] Article generated: {len(article)} chars")
    print(f"  [+] Token usage: input={usage.prompt_tokens}, output={usage.completion_tokens}")

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(article)
        print(f"  [+] Saved to {output_path}")

    return article


def _format_repos_for_prompt(repos: list[dict]) -> str:
    """将项目数据格式化为 prompt 中可读的文本"""
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
    mock_repos = [
        {"rank": i, "full_name": f"owner/repo-{i}", "url": f"https://github.com/owner/repo-{i}",
         "language": "Python", "stars_today": 100 - i * 10,
         "description": f"An amazing tool for doing amazing thing #{i}"}
        for i in range(1, 11)
    ]
    article = generate_article(mock_repos, output_path="test_article.md")
    print("\n=== Generated Article Preview ===")
    print(article[:500])
