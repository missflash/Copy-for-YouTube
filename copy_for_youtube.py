# -*- coding: utf-8 -*-
import os
import sys
import sqlite3
import shutil
import socket

import datetime

# Discord Webhook 라이브러리 체크 및 설치
try:
    from discord_webhook import DiscordWebhook, DiscordEmbed
except ImportError:
    os.system("pip3 install discord_webhook")
    from discord_webhook import DiscordWebhook, DiscordEmbed

import json

# --- Config Load ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

if not os.path.exists(CONFIG_FILE):
    print(f"Error: Config file not found at {CONFIG_FILE}")
    sys.exit(1)

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

SOURCE_DIR = config.get("source_dir")
UPLOAD_DIR = config.get("upload_dir")
COMPLETED_DIR = config.get("completed_dir")
DB_PATH = config.get("db_path")
MIN_SIZE_MB = config.get("min_size_mb", 100)
WEBHOOK_URL = config.get("webhook_url")
EXTENSIONS = tuple(config.get("extensions", (".mp4", ".mov", ".MP4", ".MOV")))

SVR_NAME = socket.gethostname().upper()

# Validation
if not all([SOURCE_DIR, UPLOAD_DIR, COMPLETED_DIR, DB_PATH]):
    print("Error: Missing required config values")
    sys.exit(1)


# --- DB 초기화 ---
def init_db():
    # DB 경로의 디렉토리가 없으면 생성
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError as e:
            print(f"Error: Cannot create database directory '{db_dir}': {e}")
            sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            filepath TEXT PRIMARY KEY,
            filename TEXT,
            status INTEGER DEFAULT 0,
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            history TEXT DEFAULT ''
        )
    """
    )

    # 기존 테이블에 history 컬럼이 없으면 추가
    try:
        cursor.execute("ALTER TABLE files ADD COLUMN history TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # 이미 존재하면 패스

    conn.commit()
    return conn


# --- 메인 로직 ---
def run_workflow(conn):
    cursor = conn.cursor()
    summary = {"new": 0, "copied": 0, "completed": 0}
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. 신규 파일 스캔
    min_size_bytes = MIN_SIZE_MB * 1024 * 1024
    extensions = EXTENSIONS
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith(extensions):
                full_path = os.path.join(root, file)
                if os.path.getsize(full_path) >= min_size_bytes:
                    cursor.execute(
                        "INSERT OR IGNORE INTO files (filepath, filename, status, history) VALUES (?, ?, 0, ?)",
                        (full_path, file, ""),
                    )
                    if cursor.rowcount > 0:
                        summary["new"] += 1

    # 2. 복사 작업 (Status 0 -> 1)
    cursor.execute("SELECT filepath, filename, history FROM files WHERE status = 0")
    for path, name, history in cursor.fetchall():
        try:
            shutil.copy2(path, os.path.join(UPLOAD_DIR, name))
            new_history = (history or "") + f"{now} : 0 -> 1\n"
            cursor.execute(
                "UPDATE files SET status = 1, history = ? WHERE filepath = ?",
                (new_history, path),
            )
            summary["copied"] += 1
        except:
            pass

    # 3. 완료 확인 (Status 1 -> 2)
    cursor.execute("SELECT filepath, filename, history FROM files WHERE status = 1")
    for path, name, history in cursor.fetchall():
        if os.path.exists(os.path.join(COMPLETED_DIR, name)):
            new_history = (history or "") + f"{now} : 1 -> 2\n"
            cursor.execute(
                "UPDATE files SET status = 2, history = ? WHERE filepath = ?",
                (new_history, path),
            )
            summary["completed"] += 1

    conn.commit()
    return summary


# --- Discord 알림 전송 ---
def send_discord_summary(summary):
    # Webhook URL이 없거나 유효하지 않으면 전송 생략
    if (
        not WEBHOOK_URL
        or WEBHOOK_URL == ""
        or "YOUR_DISCORD_WEBHOOK_URL" in WEBHOOK_URL
    ):
        print("Webhook URL is missing or invalid. Skipping Discord notification.")
        return

    webhook = DiscordWebhook(url=WEBHOOK_URL)
    embed = DiscordEmbed(
        title=f"[{SVR_NAME}] 영상 백업 워크플로우 일일 요약", color=242424
    )
    embed.set_author(name="NAS Workflow Manager")

    # 요약 정보 추가
    status_text = (
        f"🆕 새로 발견된 대용량 영상: {summary['new']}건\n"
        f"📤 Uploads 폴더 복사 완료: {summary['copied']}건\n"
        f"✅ 유튜브 업로드 및 완료 처리: {summary['completed']}건"
    )
    embed.add_embed_field(name="처리 현황 (24시간)", value=status_text, inline=False)

    # DB 통계 추가
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status, count(*) FROM files GROUP BY status")
    stats = dict(cursor.fetchall())
    total_stats = (
        f"대기: {stats.get(0,0)} / 업로드중: {stats.get(1,0)} / 완료: {stats.get(2,0)}"
    )
    embed.add_embed_field(name="누적 DB 통계", value=total_stats, inline=False)

    embed.set_timestamp()
    webhook.add_embed(embed)
    webhook.execute()


if __name__ == "__main__":
    db_conn = init_db()
    res = run_workflow(db_conn)

    # 인자값에 'notify'가 포함되어 있을 때만 디스코드 전송 (하루 한 번용)
    if len(sys.argv) > 1 and sys.argv[1] == "notify":
        send_discord_summary(res)

    db_conn.close()
