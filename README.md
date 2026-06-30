# GitHub 热榜日报

每天 9:00（北京时间）自动抓取 GitHub Trending Top 10，AI 润色后生成精美网页，部署到 GitHub Pages。

**无需服务器、无需域名、无需微信认证。** 打开网页就能看。

🌐 示例地址：`https://你的用户名.github.io/github-trending-wechat/`

## 工作原理

```
每天 9:00 GitHub Actions 自动运行
  → 抓取 github.com/trending
  → GitHub Models (Llama 3.3 70B) 生成文章
  → 构建深色主题网页
  → 部署到 GitHub Pages
```

## 使用方法

### 1. Fork 或 Clone 本仓库

### 2. 获取 GitHub Token（用于 AI 生成）

1. [github.com/settings/tokens](https://github.com/settings/tokens)
2. Generate new token (classic) → 不用勾任何权限
3. 复制 token

### 3. 配置 GitHub Secrets

Settings → Secrets and variables → Actions → New repository secret：

| Name | Value |
|------|-------|
| `GH_PAT` | 你的 GitHub Token |

> 只需要这一个 Secret。不需要微信 AppID/AppSecret，不需要 IP 白名单。

### 4. 启用 GitHub Pages

Settings → Pages → Source: **Deploy from a branch** → Branch: `gh-pages` `/ (root)` → Save

等 1 分钟后访问 `https://你的用户名.github.io/github-trending-wechat/`

### 5. 手动测试

Actions → Daily GitHub Trending Publish → Run workflow

## 接入微信公众号

公众号后台 → 自定义菜单 → 添加菜单项：
- 菜单名：**今日热榜**
- 类型：跳转网页
- URL：`https://你的用户名.github.io/github-trending-wechat/`

用户关注后点击菜单即可查看每日热榜。

## 项目结构

```
github-trending-wechat/
├── .github/workflows/daily-publish.yml   # 定时触发 + 部署
├── src/
│   ├── main.py                           # 主流程
│   ├── fetch_trending.py                 # 抓取 GitHub Trending
│   ├── generate_article.py               # GitHub Models 生成文章
│   └── build_page.py                     # 构建深色主题网页
├── docs/                                 # 网页输出目录
│   ├── index.html                        # 今日热榜
│   └── archive/                          # 历史归档
├── templates/prompt.md                   # AI 写作风格
└── output/                               # 生成数据（可查看）
```

## 费用

**零。** 全部免费。

| 环节 | 费用 |
|------|------|
| GitHub Trending 抓取 | 免费 |
| GitHub Models AI 生成 | 免费 |
| GitHub Actions 调度 | 免费（公开仓库） |
| GitHub Pages 托管 | 免费 |
