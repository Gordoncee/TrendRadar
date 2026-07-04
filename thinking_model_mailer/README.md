# 多元思维模型每日邮件自动化

这个项目会每天早上 7 点（北京时间）自动发送一封「多元思维模型」HTML 邮件。它不依赖 Codex，也不依赖你的电脑开机；部署后由 GitHub Actions 在云端定时运行。

## 文件说明

- `send_daily_model.py`：生成并发送邮件的 Python 脚本，无第三方依赖。
- `lessons.json`：模型内容库，目前内置 12 个核心模型。
- `.github/workflows/daily-thinking-model.yml`：GitHub Actions 定时任务。
- `.env.example`：本地测试或配置 GitHub Secrets 时的字段参考。
- `preview.html`：本地预览生成后会出现，用来查看邮件样式。

## 部署步骤

### 方案 A：放进 TrendRadar 仓库，直接复用 Outlook 配置

你的 `Gordoncee/TrendRadar` 仓库已经使用邮件推送，并且它的 GitHub Secrets 命名是：

- `EMAIL_FROM`
- `EMAIL_PASSWORD`
- `EMAIL_TO`
- `EMAIL_SMTP_SERVER`（可选）
- `EMAIL_SMTP_PORT`（可选）

本项目已经兼容这组命名。也就是说，如果你把本项目文件放进 `Gordoncee/TrendRadar` 仓库，通常不需要重新生成 Outlook 授权码。

最简单的做法：

1. 把 `thinking_model_mailer/` 文件夹放到 `Gordoncee/TrendRadar` 仓库根目录。
2. 把 `.github/workflows/daily-thinking-model.yml` 放到该仓库的 `.github/workflows/` 目录。
3. 进入仓库 `Actions`，手动运行 `Daily Thinking Model Email` 测试。

脚本会优先读取本项目自己的变量名，也会兼容 TrendRadar 的 `EMAIL_*` 变量名。如果 `EMAIL_SMTP_SERVER` 和 `EMAIL_SMTP_PORT` 没有配置，会根据发件邮箱自动识别 Outlook：

- `outlook.com` / `hotmail.com` / `live.com`
- SMTP：`smtp-mail.outlook.com`
- 端口：`587`
- 加密：`STARTTLS`

### 方案 B：新建独立仓库

1. 在 GitHub 新建一个私有仓库，比如 `thinking-model-mailer`。
2. 把本文件夹里的所有文件上传到仓库根目录。注意要包含隐藏目录 `.github/workflows/`。
3. 打开仓库的 `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`。
4. 添加下面这些 Secrets：

| 名称 | 说明 |
| --- | --- |
| `SMTP_HOST` | 邮箱 SMTP 服务器，例如 `smtp.qq.com`、`smtp.163.com`、`smtp.gmail.com` |
| `SMTP_PORT` | SSL 通常填 `465`，STARTTLS 通常填 `587` |
| `SMTP_SECURITY` | `ssl` 或 `starttls` |
| `SMTP_USER` | 发件邮箱账号 |
| `SMTP_PASSWORD` | SMTP 授权码或应用专用密码，不是普通登录密码 |
| `MAIL_FROM` | 发件邮箱 |
| `MAIL_FROM_NAME` | 发件人名称，例如 `多元思维模型` |
| `MAIL_TO` | 收件邮箱，也就是你要接收邮件的地址 |
| `SUBJECT_PREFIX` | 邮件标题前缀，可填 `多元思维模型` |

## 常见邮箱配置

| 邮箱 | SMTP_HOST | SMTP_PORT | SMTP_SECURITY | 密码 |
| --- | --- | --- | --- | --- |
| QQ 邮箱 | `smtp.qq.com` | `465` | `ssl` | QQ 邮箱生成的 SMTP 授权码 |
| 163 邮箱 | `smtp.163.com` | `465` | `ssl` | 163 邮箱客户端授权码 |
| Gmail | `smtp.gmail.com` | `587` | `starttls` | Google 应用专用密码 |
| Outlook | `smtp.office365.com` | `587` | `starttls` | Outlook 应用密码或账号密码，取决于账号设置 |

## 测试发送

上传并配置 Secrets 后：

1. 进入仓库的 `Actions`。
2. 选择 `Daily Thinking Model Email`。
3. 点击 `Run workflow`。
4. 等运行完成后，检查收件邮箱。

## 定时规则

GitHub Actions 的定时任务使用 UTC 时间：

```yaml
cron: "0 23 * * *"
```

北京时间是 UTC+8，所以每天 UTC 23:00 会对应北京时间第二天 07:00。

## 如何追加更多模型

打开 `lessons.json`，按现有格式继续添加：

```json
{
  "id": "013",
  "title": "模型名称",
  "discipline": "学科 · 主题",
  "core_sentence": "一句话解释",
  "what_it_solves": "它解决什么问题",
  "fable_title": "寓言标题",
  "fable": ["第一段", "第二段"],
  "deep_explanation": ["深入解释第一段", "深入解释第二段"],
  "life_examples": [
    {
      "title": "例子标题",
      "context": "生活场景",
      "model_view": "模型视角",
      "action": "行动提醒"
    }
  ],
  "call_scenarios": ["什么时候调用它"],
  "misuse": ["最容易误用的地方"],
  "reflection_questions": ["自问问题"],
  "today_practice": {
    "intro": "练习说明",
    "template": "练习模板"
  },
  "memory_sentence": "今日金句"
}
```

脚本会从 `START_DATE` 开始按天发送。如果内容库发送完，会从第一个模型重新循环。

## 本地预览

如果你想在上传前看邮件样式，可以在本地运行：

```bash
python send_daily_model.py --dry-run --lesson 1 --output preview.html
```

然后打开 `preview.html` 查看效果。

## 小提醒

GitHub 的免费定时任务通常足够个人使用，但它不是金融级精确定时系统，偶尔可能延迟几分钟。对你的场景来说问题不大：每天早上自动收到即可。
