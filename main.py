from db_setup  import init_db, DB_PATH
from crawler   import main as run_crawler
from sentiment import run_sentiment
from analysis  import export_for_tableau, detect_issue_spike
from notify    import get_summary, send_slack
import sqlite3

def main():
    print("\n[1/5] DB 초기화")
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE reviews SET sentiment = NULL")
    conn.commit()
    conn.close()

    print("\n[2/5] 크롤링 시작")
    run_crawler()

    print("\n[3/5] 감성 분석")
    run_sentiment()

    print("\n[4/5] 이슈 감지 & CSV 내보내기")
    detect_issue_spike()
    export_for_tableau()

    print("\n[5/5] Slack 알림 전송")
    send_slack(get_summary())
    
if __name__ == "__main__":
    main()