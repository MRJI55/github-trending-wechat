"""
微信公众号 API 封装模块。

支持三个核心操作：
1. 获取 access_token
2. 创建草稿
3. 发布（个人订阅号每天1次）

参考文档: https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html
"""

import os
import time
import requests
from datetime import datetime
from typing import Optional

WECHAT_API_BASE = "https://api.weixin.qq.com"


class WeChatAPI:
    """微信公众号 API 客户端"""

    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        self.app_id = app_id or os.environ.get("WECHAT_APP_ID")
        self.app_secret = app_secret or os.environ.get("WECHAT_APP_SECRET")
        if not self.app_id or not self.app_secret:
            raise ValueError(
                "WECHAT_APP_ID and WECHAT_APP_SECRET must be set. "
                "Pass them directly or set as environment variables."
            )
        self._token: Optional[str] = None
        self._token_expires_at: float = 0

    # ── token 管理 ──────────────────────────────────

    def get_access_token(self) -> str:
        """获取 access_token（自动缓存和刷新）"""
        if self._token and time.time() < self._token_expires_at - 300:
            return self._token

        url = f"{WECHAT_API_BASE}/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret,
        }
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"Failed to get access_token: {data}")

        self._token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 7200)
        print(f"  [+] Got access_token (expires in {data.get('expires_in')}s)")
        return self._token

    # ── 草稿管理 ────────────────────────────────────

    def create_draft(self, title: str, content: str) -> str:
        """
        创建草稿。

        Args:
            title: 文章标题
            content: 文章内容（支持 HTML 或纯文本，最多 20000 字符）

        Returns:
            media_id: 草稿的 media_id（用于后续发布）
        """
        token = self.get_access_token()
        url = f"{WECHAT_API_BASE}/cgi-bin/draft/add?access_token={token}"

        body = {
            "articles": [
                {
                    "title": title,
                    "content": content,
                    "content_source_url": "",
                    "need_open_comment": 0,
                    "only_fans_can_comment": 0,
                }
            ]
        }

        resp = requests.post(url, json=body, timeout=30)
        data = resp.json()

        if "media_id" not in data:
            raise RuntimeError(f"Failed to create draft: {data}")

        media_id = data["media_id"]
        print(f"  [+] Draft created: media_id={media_id}")
        return media_id

    # ── 发布 ────────────────────────────────────────

    def publish(self, media_id: str) -> dict:
        """
        发布草稿（个人订阅号调用 free_publish 接口）。

        Args:
            media_id: 草稿的 media_id

        Returns:
            API 响应数据
        """
        token = self.get_access_token()
        url = f"{WECHAT_API_BASE}/cgi-bin/freepublish/submit?access_token={token}"

        body = {"media_id": media_id}

        resp = requests.post(url, json=body, timeout=30)
        data = resp.json()

        if data.get("errcode") == 0:
            publish_id = data.get("publish_id", "N/A")
            print(f"  [+] Published! publish_id={publish_id}")
        else:
            raise RuntimeError(f"Failed to publish: {data}")

        return data


def publish_article(
    title: str,
    content: str,
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    auto_publish: bool = True,
) -> dict:
    """
    一站式：创建草稿 → 发布。

    Args:
        title: 文章标题
        content: 文章内容（Markdown 或纯文本）
        app_id: 公众号 AppID
        app_secret: 公众号 AppSecret
        auto_publish: 是否自动发布（False 则只创建草稿）

    Returns:
        包含 media_id 和发布结果的字典
    """
    client = WeChatAPI(app_id=app_id, app_secret=app_secret)

    # 截断超长内容
    if len(content) > 20000:
        print(f"  [!] Content too long ({len(content)} chars), truncating to 20000")
        content = content[:20000]

    print(f"[{datetime.now().isoformat()}] Creating WeChat draft...")
    media_id = client.create_draft(title, content)

    result = {"media_id": media_id, "published": False}

    if auto_publish:
        print(f"[{datetime.now().isoformat()}] Publishing...")
        pub_result = client.publish(media_id)
        result["publish_result"] = pub_result
        result["published"] = True
    else:
        print("  [*] auto_publish=False, draft saved but not published")

    return result


if __name__ == "__main__":
    # 测试：只创建草稿（不发布）
    publish_article(
        title="【测试】GitHub Trending 日报 — " + datetime.now().strftime("%m月%d日"),
        content="<p>这是一篇测试文章，由 <b>github-trending-wechat</b> 自动生成。</p>",
        auto_publish=False,
    )
