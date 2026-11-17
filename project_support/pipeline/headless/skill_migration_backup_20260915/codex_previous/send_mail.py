#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发送每日流水线状态汇总邮件 (QQ 邮箱 SMTP)。

用法:
    python send_mail.py '<邮件正文>'
    python send_mail.py '<邮件正文>' '邮件主题'

凭据从 ~/.claude/smtp_config.json 读取。
"""
import json
import os
import smtplib
import sys
from email.header import Header
from email.mime.text import MIMEText

CONFIG = os.path.join(os.path.expanduser("~"), ".claude", "smtp_config.json")


def main():
    if len(sys.argv) < 2:
        print("用法: python send_mail.py '<正文>' [主题]")
        sys.exit(1)

    body = sys.argv[1]
    subject = sys.argv[2] if len(sys.argv) > 2 else "流水线每日状态汇总"

    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)

    if "PLEASE_FILL" in cfg.get("from_addr", "") or "PLEASE_FILL" in cfg.get("smtp_code", ""):
        print("错误: 请先填写 ~/.claude/smtp_config.json 中的 from_addr 和 smtp_code (QQ 邮箱授权码)")
        sys.exit(2)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = cfg["from_addr"]
    msg["To"] = cfg["to_addr"]

    try:
        server = smtplib.SMTP_SSL(cfg["smtp_host"], cfg["smtp_port"], timeout=30)
        server.login(cfg["from_addr"], cfg["smtp_code"])
        server.sendmail(cfg["from_addr"], [cfg["to_addr"]], msg.as_string())
        server.quit()
        print("邮件已发送到 %s" % cfg["to_addr"])
    except Exception as e:
        print("发送失败: %s" % e)
        sys.exit(1)


if __name__ == "__main__":
    main()
