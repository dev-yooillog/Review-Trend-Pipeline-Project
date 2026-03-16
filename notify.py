"""
notify.py — Slack 웹훅 알림
GitHub Actions 마지막 단계에서 실행
"""

import os
import json
import sqlite3
import requests
from db_setup import DB_PATH

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL", "")


def get_summary() -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM reviews")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM reviews
        WHERE DATE(collected_at) = DATE('now')
    """)
    today_new = cur.fetchone()[0]

    cur.execute("""
        SELECT sentiment, COUNT(*) FROM reviews
        WHERE sentiment IS NOT NULL
        GROUP BY sentiment
    """)
    sentiment_counts = dict(cur.fetchall())

    cur.execute("""
        SELECT k.keyword, COUNT(*) AS cnt
        FROM keywords k
        JOIN reviews r ON k.review_id = r.review_id
        WHERE r.sentiment = 'negative'
        GROUP BY k.keyword
        ORDER BY cnt DESC LIMIT 3
    """)
    top_neg_kw = [row[0] for row in cur.fetchall()]

    conn.close()
    return {
        "total":      total,
        "today_new":  today_new,
        "sentiments": sentiment_counts,
        "top_neg":    top_neg_kw,
    }


def send_slack(summary: dict):
    if not SLACK_WEBHOOK:
        print("⚠️  SLACK_WEBHOOK_URL 환경변수가 없습니다.")
        return

    pos = summary["sentiments"].get("positive", 0)
    neg = summary["sentiments"].get("negative", 0)
    neu = summary["sentiments"].get("neutral",  0)

    text = (
        f"*📊 주간 리뷰 수집 완료*\n"
        f"• 이번 주 신규: *{summary['today_new']:,}건*\n"
        f"• 누적 전체:    *{summary['total']:,}건*\n"
        f"• 감성 비율: 긍정 {pos} / 부정 {neg} / 중립 {neu}\n"
        f"• 부정 상위 키워드: `{'`, `'.join(summary['top_neg'])}`"
    )

    resp = requests.post(
        SLACK_WEBHOOK,
        data=json.dumps({"text": text}),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if resp.status_code == 200:
        print("✅ Slack 알림 전송 완료")
    else:
        print(f"⚠️  Slack 전송 실패: {resp.status_code}")


if __name__ == "__main__":
    summary = get_summary()
    send_slack(summary)
    print(summary)
