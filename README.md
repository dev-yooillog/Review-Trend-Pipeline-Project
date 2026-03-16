# 생활가전 리뷰 트렌드 모니터링 시스템

네이버쇼핑 생활가전 리뷰를 자동 수집·분석하는 데이터 파이프라인

## 프로젝트 구조

```
├── main.py              # 전체 파이프라인 진입점
├── db_setup.py          # SQLite DB 초기화
├── crawler.py           # 네이버쇼핑 크롤러
├── sentiment.py         # 감성 분석 + 키워드 추출
├── analysis.py          # SQL 분석 쿼리 + CSV 내보내기
├── notify.py            # Slack 웹훅 알림
├── requirements.txt
└── .github/
    └── workflows/
        └── crawl.yml    # GitHub Actions 자동화
```

## 실행 방법

### 로컬 실행
```bash
pip install -r requirements.txt

export NAVER_CLIENT_ID=your_id
export NAVER_CLIENT_SECRET=your_secret
export SLACK_WEBHOOK_URL=your_webhook

python main.py
```

### GitHub Actions 자동 실행 설정

1. GitHub repo → Settings → Secrets → Actions
2. 아래 3개 Secret 등록:
   - `NAVER_CLIENT_ID`
   - `NAVER_CLIENT_SECRET`
   - `SLACK_WEBHOOK_URL`
3. 매주 월요일 오전 9시 자동 실행
4. Actions 탭 → "주간 리뷰 수집 파이프라인" → Run workflow (수동 실행)

## 네이버 API 발급

1. https://developers.naver.com 접속
2. 애플리케이션 등록 → 쇼핑 검색 API 선택
3. Client ID / Secret 발급 (무료, 일 1만건)

## Slack Webhook 설정

1. https://api.slack.com/apps → Create App
2. Incoming Webhooks → Activate → Add New Webhook
3. 채널 선택 → Webhook URL 복사

## 산출물

- `tableau_reviews.csv` — 리뷰 원본 + 감성 레이블
- `tableau_keywords.csv` — 키워드 빈도 데이터
- Tableau Public에서 위 CSV 연결 후 대시보드 제작
