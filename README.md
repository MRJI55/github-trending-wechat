# GitHub Trending 微信日报

每天 9:00（北京时间）自动抓取 GitHub Trending Top 10，AI 润色后发布到微信公众号。

**免费方案**：AI 生成使用 GitHub Models（零费用），无需注册任何外部 AI 服务。

## 使用方法

### 1. 注册微信公众号

访问 [mp.weixin.qq.com](https://mp.weixin.qq.com) 注册个人订阅号，获取：
- AppID（开发 → 基本配置）
- AppSecret（开发 → 基本配置）

### 2. 获取 GitHub Token（用于 AI 生成）

1. 打开 [GitHub Tokens](https://github.com/settings/tokens)
2. 点击 Generate new token (classic)
3. 勾选 `repo` 和 `workflow` 权限
4. 生成并复制 token

> 注意：如果是公开仓库，不需要任何额外权限即可使用 GitHub Models 的免费额度。

### 3. 配置 GitHub Secrets

在仓库 Settings → Secrets and variables → Actions 中添加：

| Secret 名称 | 值 |
|-------------|-----|
| `WECHAT_APP_ID` | 公众号 AppID |
| `WECHAT_APP_SECRET` | 公众号 AppSecret |
| `GH_PAT` | GitHub Personal Access Token |

### 4. 本地测试

```bash
# 设置环境变量
export WECHAT_APP_ID=your_app_id
export WECHAT_APP_SECRET=your_app_secret
export GITHUB_TOKEN=your_github_token

# 安装依赖
pip install -r requirements.txt

# 完整流程测试
python src/main.py
```

### 5. 启用定时任务

推送代码到 GitHub `main` 分支，GitHub Actions 将每天 9:00 自动运行。

也可以手动触发：Actions → Daily Publish → Run workflow。

## 费用

| 环节 | 费用 |
|------|------|
| GitHub Trending 抓取 | 免费 |
| GitHub Models AI 生成 | **免费**（Llama 3.3 70B） |
| 微信公众号 | 免费（个人订阅号） |
| GitHub Actions | 免费（公开仓库无限分钟） |

**零费用运行。**

## 项目结构

```
github-trending-wechat/
├── .github/workflows/daily-publish.yml   # 定时触发器
├── src/
│   ├── main.py                           # 主流程编排
│   ├── fetch_trending.py                 # 抓取 GitHub Trending
│   ├── generate_article.py               # GitHub Models 生成文章
│   └── wechat_api.py                     # 微信 API 封装
├── templates/prompt.md                   # AI 写作风格指南
├── docs/OUTPUT_EXAMPLE.md                # 生成文章示例
├── requirements.txt
└── README.md
```

## 注意事项

- 个人订阅号每天只能发布 1 次
- 首次使用需要在微信公众号后台配置 **IP 白名单**（添加 GitHub Actions 出口 IP）
- GitHub Models 免费额度对公开仓库足够使用
- 如果某天 AI 生成失败，会自动降级到模板文章，不会中断发布
