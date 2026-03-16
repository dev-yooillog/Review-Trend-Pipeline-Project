from db_setup  import init_db
from crawler   import main as run_crawler
from sentiment import run_sentiment
from analysis  import export_for_tableau, detect_issue_spike
from notify    import get_summary, send_slack


def main():
    # 1. DB 초기화
    init_db()

    # 2. 크롤링
    run_crawler()

    # 3. 감성 분석
    run_sentiment()

    # 4. 이슈 감지 + Tableau CSV 
    detect_issue_spike()
    export_for_tableau()

    # 5. Slack 알림
    summary = get_summary()
    send_slack(summary)
    
    print("완료!")


if __name__ == "__main__":
    main()
