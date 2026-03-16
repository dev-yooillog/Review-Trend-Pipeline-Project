from db_setup  import init_db
from crawler   import main as run_crawler
from sentiment import run_sentiment
from analysis  import export_for_tableau, detect_issue_spike
from notify    import get_summary, send_slack


def main():
    # 1. DB 초기화 (테이블 없으면 생성)
    print("\n[1/5] DB 초기화")
    init_db()

    # 2. 크롤링
    print("\n[2/5] 크롤링 시작")
    run_crawler()

    # 3. 감성 분석
    print("\n[3/5] 감성 분석")
    run_sentiment()

    # 4. 이슈 감지 + Tableau CSV 내보내기
    print("\n[4/5] 이슈 감지 & CSV 내보내기")
    detect_issue_spike()
    export_for_tableau()

    # 5. Slack 알림
    print("\n[5/5] Slack 알림 전송")
    summary = get_summary()
    send_slack(summary)

    print("\n" + "=" * 50)
    print("파이프라인 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
