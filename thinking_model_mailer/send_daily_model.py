#!/usr/bin/env python3
"""
Daily mental-model email sender.

Runs locally or in GitHub Actions. By default it selects today's lesson by
counting days from START_DATE in Asia/Shanghai, renders a polished HTML email,
and sends it through SMTP.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent
LESSONS_PATH = BASE_DIR / "lessons.json"


SMTP_CONFIGS = {
    "gmail.com": {"server": "smtp.gmail.com", "port": 587, "security": "starttls"},
    "qq.com": {"server": "smtp.qq.com", "port": 465, "security": "ssl"},
    "outlook.com": {"server": "smtp-mail.outlook.com", "port": 587, "security": "starttls"},
    "hotmail.com": {"server": "smtp-mail.outlook.com", "port": 587, "security": "starttls"},
    "live.com": {"server": "smtp-mail.outlook.com", "port": 587, "security": "starttls"},
    "163.com": {"server": "smtp.163.com", "port": 465, "security": "ssl"},
    "126.com": {"server": "smtp.126.com", "port": 465, "security": "ssl"},
    "sina.com": {"server": "smtp.sina.com", "port": 465, "security": "ssl"},
    "sohu.com": {"server": "smtp.sohu.com", "port": 465, "security": "ssl"},
    "189.cn": {"server": "smtp.189.cn", "port": 465, "security": "ssl"},
    "aliyun.com": {"server": "smtp.aliyun.com", "port": 465, "security": "ssl"},
    "yandex.com": {"server": "smtp.yandex.com", "port": 465, "security": "ssl"},
    "icloud.com": {"server": "smtp.mail.me.com", "port": 587, "security": "starttls"},
}


def first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ""


def require_first_env(*names: str) -> str:
    value = first_env(*names)
    if not value:
        joined = " or ".join(names)
        raise RuntimeError(f"Missing required environment variable: {joined}")
    return value


def infer_smtp_config(email_address: str) -> tuple[str, int, str]:
    domain = email_address.split("@")[-1].lower()
    config = SMTP_CONFIGS.get(domain)
    if config:
        return config["server"], int(config["port"]), config["security"]
    return f"smtp.{domain}", 587, "starttls"


def load_lessons() -> list[dict]:
    with LESSONS_PATH.open("r", encoding="utf-8") as f:
        lessons = json.load(f)
    if not isinstance(lessons, list) or not lessons:
        raise RuntimeError("lessons.json must contain a non-empty list.")
    return lessons


def today_in_timezone(tz_name: str) -> dt.date:
    return dt.datetime.now(ZoneInfo(tz_name)).date()


def select_lesson(lessons: list[dict], tz_name: str, start_date: str, lesson_no: int | None) -> tuple[dict, int]:
    if lesson_no is not None:
        if lesson_no < 1 or lesson_no > len(lessons):
            raise ValueError(f"--lesson must be between 1 and {len(lessons)}")
        return lessons[lesson_no - 1], lesson_no

    start = dt.date.fromisoformat(start_date)
    today = today_in_timezone(tz_name)
    elapsed = max((today - start).days, 0)
    index = elapsed % len(lessons)
    return lessons[index], elapsed + 1


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_list(items: list[str]) -> str:
    return "".join(f"<li>{esc(item)}</li>" for item in items)


def render_paragraphs(paragraphs: list[str]) -> str:
    return "".join(f"<p>{esc(p)}</p>" for p in paragraphs)


def render_examples(examples: list[dict]) -> str:
    parts = []
    for item in examples:
        parts.append(
            f"""
            <div class="example">
              <div class="example-title">{esc(item["title"])}</div>
              <p><strong>场景：</strong>{esc(item["context"])}</p>
              <p><strong>模型视角：</strong>{esc(item["model_view"])}</p>
              <p><strong>行动提醒：</strong>{esc(item["action"])}</p>
            </div>
            """
        )
    return "".join(parts)


def render_html(lesson: dict, day_number: int, send_date: dt.date) -> str:
    examples = render_examples(lesson["life_examples"])
    call_scenarios = render_list(lesson["call_scenarios"])
    misuse = render_list(lesson["misuse"])
    reflection = render_list(lesson["reflection_questions"])
    fable = render_paragraphs(lesson["fable"])
    deep = render_paragraphs(lesson["deep_explanation"])

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(lesson["title"])}</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background: #f4f1ea;
      color: #202124;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
      line-height: 1.72;
    }}
    .wrap {{
      width: 100%;
      padding: 28px 0;
      background: #f4f1ea;
    }}
    .container {{
      max-width: 720px;
      margin: 0 auto;
      background: #fffdf8;
      border: 1px solid #e7ddca;
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 18px 48px rgba(60, 48, 30, 0.11);
    }}
    .hero {{
      padding: 34px 38px 30px;
      background: linear-gradient(135deg, #263238 0%, #475a54 45%, #b77c43 100%);
      color: #fff;
    }}
    .eyebrow {{
      font-size: 13px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      opacity: .82;
      margin: 0 0 12px;
    }}
    h1 {{
      margin: 0;
      font-size: 31px;
      line-height: 1.22;
      letter-spacing: 0;
    }}
    .subtitle {{
      margin: 16px 0 0;
      font-size: 16px;
      opacity: .94;
    }}
    .content {{
      padding: 34px 38px 38px;
    }}
    h2 {{
      margin: 30px 0 12px;
      font-size: 20px;
      line-height: 1.35;
      color: #24312d;
    }}
    h2:first-child {{
      margin-top: 0;
    }}
    p {{
      margin: 10px 0;
      font-size: 16px;
    }}
    .card {{
      margin: 18px 0;
      padding: 18px 20px;
      border-radius: 12px;
      background: #f8f4ec;
      border: 1px solid #eadfcd;
    }}
    .principle {{
      border-left: 5px solid #b77c43;
      background: #fff8ed;
      padding: 16px 18px;
      margin: 18px 0;
      border-radius: 10px;
      font-size: 17px;
      font-weight: 650;
      color: #3a2c1d;
    }}
    .example {{
      margin: 14px 0;
      padding: 16px 18px;
      border: 1px solid #e8dfd1;
      border-radius: 12px;
      background: #ffffff;
    }}
    .example-title {{
      font-weight: 700;
      color: #263238;
      margin-bottom: 6px;
    }}
    ul {{
      margin: 10px 0 0 20px;
      padding: 0;
    }}
    li {{
      margin: 7px 0;
    }}
    .practice {{
      margin-top: 28px;
      padding: 22px;
      border-radius: 14px;
      background: #263238;
      color: #fff;
    }}
    .practice h2 {{
      color: #fff;
      margin-top: 0;
    }}
    .practice code {{
      display: block;
      white-space: pre-wrap;
      background: rgba(255,255,255,.1);
      padding: 14px 16px;
      border-radius: 10px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      line-height: 1.7;
    }}
    .footer {{
      padding: 22px 38px 30px;
      color: #73695b;
      font-size: 13px;
      border-top: 1px solid #e7ddca;
      background: #f8f4ec;
    }}
    @media (max-width: 640px) {{
      .wrap {{ padding: 0; }}
      .container {{ border-radius: 0; border-left: 0; border-right: 0; }}
      .hero, .content, .footer {{ padding-left: 22px; padding-right: 22px; }}
      h1 {{ font-size: 26px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="container">
      <div class="hero">
        <div class="eyebrow">Mental Model · Day {day_number} · {esc(send_date.isoformat())}</div>
        <h1>{esc(lesson["id"])}｜{esc(lesson["title"])}</h1>
        <p class="subtitle">{esc(lesson["discipline"])} · 用一个模型，把今天想清楚一点。</p>
      </div>
      <div class="content">
        <h2>一句话解释</h2>
        <div class="principle">{esc(lesson["core_sentence"])}</div>

        <h2>它解决什么问题</h2>
        <p>{esc(lesson["what_it_solves"])}</p>

        <h2>寓言故事：{esc(lesson["fable_title"])}</h2>
        <div class="card">{fable}</div>

        <h2>再深入一层</h2>
        {deep}

        <h2>生活中的例子</h2>
        {examples}

        <h2>什么时候调用它</h2>
        <ul>{call_scenarios}</ul>

        <h2>最容易误用的地方</h2>
        <ul>{misuse}</ul>

        <h2>三个自问</h2>
        <ul>{reflection}</ul>

        <div class="practice">
          <h2>今日练习</h2>
          <p>{esc(lesson["today_practice"]["intro"])}</p>
          <code>{esc(lesson["today_practice"]["template"])}</code>
        </div>

        <h2>今天记住这一句</h2>
        <div class="principle">{esc(lesson["memory_sentence"])}</div>
      </div>
      <div class="footer">
        这封邮件由你的「多元思维模型」自动化发送。慢慢来，模型不是拿来炫耀的，是拿来让生活少一点混沌的。
      </div>
    </div>
  </div>
</body>
</html>
"""


def render_text(lesson: dict, day_number: int, send_date: dt.date) -> str:
    lines = [
        f"多元思维模型 Day {day_number} · {send_date.isoformat()}",
        f"{lesson['id']}｜{lesson['title']}",
        "",
        f"一句话解释：{lesson['core_sentence']}",
        "",
        f"它解决什么问题：{lesson['what_it_solves']}",
        "",
        f"寓言故事：{lesson['fable_title']}",
        *lesson["fable"],
        "",
        "再深入一层：",
        *lesson["deep_explanation"],
        "",
        "今日练习：",
        lesson["today_practice"]["intro"],
        lesson["today_practice"]["template"],
        "",
        f"今天记住这一句：{lesson['memory_sentence']}",
    ]
    return "\n".join(lines)


def build_message(lesson: dict, day_number: int, send_date: dt.date) -> EmailMessage:
    mail_from = require_first_env("MAIL_FROM", "EMAIL_FROM")
    mail_to = require_first_env("MAIL_TO", "EMAIL_TO")
    from_name = os.getenv("MAIL_FROM_NAME") or "多元思维模型"

    subject_prefix = os.getenv("SUBJECT_PREFIX") or "多元思维模型"
    subject = f"{subject_prefix} Day {day_number}: {lesson['title']}"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((from_name, mail_from))
    message["To"] = mail_to
    message.set_content(render_text(lesson, day_number, send_date))
    message.add_alternative(render_html(lesson, day_number, send_date), subtype="html")
    return message


def send_message(message: EmailMessage) -> None:
    username = require_first_env("SMTP_USER", "EMAIL_FROM", "MAIL_FROM")
    password = require_first_env("SMTP_PASSWORD", "EMAIL_PASSWORD")

    inferred_host, inferred_port, inferred_security = infer_smtp_config(username)
    host = first_env("SMTP_HOST", "EMAIL_SMTP_SERVER") or inferred_host
    security_mode = (first_env("SMTP_SECURITY") or inferred_security).lower()
    default_port = 465 if security_mode == "ssl" else inferred_port
    port_text = first_env("SMTP_PORT", "EMAIL_SMTP_PORT")
    port = int(port_text) if port_text else int(default_port)

    if security_mode == "ssl":
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(username, password)
            server.send_message(message)
    elif security_mode == "starttls":
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(username, password)
            server.send_message(message)
    else:
        with smtplib.SMTP(host, port) as server:
            server.login(username, password)
            server.send_message(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lesson", type=int, help="Send or preview a specific lesson number, starting from 1.")
    parser.add_argument("--dry-run", action="store_true", help="Render HTML but do not send email.")
    parser.add_argument("--output", default="preview.html", help="Output path for --dry-run.")
    args = parser.parse_args()

    tz_name = os.getenv("TZ_NAME") or "Asia/Shanghai"
    start_date = os.getenv("START_DATE") or today_in_timezone(tz_name).isoformat()
    send_date = today_in_timezone(tz_name)

    lessons = load_lessons()
    lesson, day_number = select_lesson(lessons, tz_name, start_date, args.lesson)

    if args.dry_run:
        output = Path(args.output)
        output.write_text(render_html(lesson, day_number, send_date), encoding="utf-8")
        print(f"Preview written to {output.resolve()}")
        return

    message = build_message(lesson, day_number, send_date)
    send_message(message)
    print(f"Sent lesson {lesson['id']} to {message['To']}")


if __name__ == "__main__":
    main()
