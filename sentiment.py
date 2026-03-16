"""
sentiment.py — 리뷰 감성 분석 + 키워드 추출
- VADER 기반 한국어 규칙 감성 분류 (별점 보조)
- konlpy Okt로 명사 키워드 추출
- 미분류 리뷰만 처리해서 재실행 가능
"""

import sqlite3
import re
from collections import Counter
from db_setup import DB_PATH

# 긍정 / 부정 키워드 사전 (도메인 특화)
POSITIVE_WORDS = {
    "좋아요", "좋습니다", "만족", "추천", "완벽", "훌륭", "최고", "편리",
    "깔끔", "조용", "강력", "빠르", "효과", "가성비", "괜찮", "기대이상",
    "예쁘", "디자인", "튼튼", "잘됩니", "잘돼", "잘 돼",
}
NEGATIVE_WORDS = {
    "불만", "최악", "별로", "실망", "후회", "불편", "고장", "소음",
    "시끄럽", "냄새", "약함", "느림", "환불", "반품", "비추", "문제",
    "오류", "작동안", "안됩니", "아쉽", "별로", "그냥저냥",
}


def simple_sentiment(text: str, star: int) -> str:
    """규칙 기반 감성 분류 (별점 우선, 키워드 보조)"""
    if star >= 4:
        return "positive"
    if star <= 2:
        return "negative"

    # 별점 3점: 키워드로 판별
    pos = sum(1 for w in POSITIVE_WORDS if w in text)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text)

    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def extract_keywords(text: str) -> list[str]:
    """
    konlpy 없이도 동작하는 간이 명사 추출
    (실제 프로젝트에선 konlpy Okt 권장)
    """
    try:
        from konlpy.tag import Okt
        okt = Okt()
        nouns = okt.nouns(text)
        return [n for n in nouns if len(n) >= 2]

    except ImportError:
        # konlpy 미설치 시 — 2글자 이상 한글 토큰 추출 (간이)
        tokens = re.findall(r"[가-힣]{2,5}", text)
        stopwords = {"그리고", "하지만", "그래서", "이게", "저도", "정말", "너무", "진짜"}
        return [t for t in tokens if t not in stopwords]


def run_sentiment():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # 아직 감성 분류 안 된 리뷰만
    cur.execute("""
        SELECT review_id, review_text, star_rating
        FROM reviews
        WHERE sentiment IS NULL
    """)
    rows = cur.fetchall()
    print(f"🔍 미분류 리뷰 {len(rows)}건 처리 시작")

    keyword_rows = []
    updated = 0

    for review_id, text, star in rows:
        sentiment = simple_sentiment(text, star)
        keywords  = extract_keywords(text)
        freq      = Counter(keywords)

        cur.execute("""
            UPDATE reviews SET sentiment = ? WHERE review_id = ?
        """, (sentiment, review_id))

        for kw, cnt in freq.items():
            keyword_rows.append((review_id, kw, cnt))

        updated += 1
        if updated % 100 == 0:
            print(f"  ...{updated}건 처리 중")

    # 키워드 저장
    cur.executemany("""
        INSERT OR IGNORE INTO keywords (review_id, keyword, frequency)
        VALUES (?, ?, ?)
    """, keyword_rows)

    conn.commit()
    conn.close()

    # 결과 요약
    conn2 = sqlite3.connect(DB_PATH)
    cur2  = conn2.cursor()
    cur2.execute("""
        SELECT sentiment, COUNT(*) FROM reviews
        WHERE sentiment IS NOT NULL
        GROUP BY sentiment
    """)
    summary = cur2.fetchall()
    conn2.close()

    print("\n📊 감성 분석 결과:")
    for sentiment, cnt in summary:
        print(f"  {sentiment:10s}: {cnt:,}건")
    print(f"\n✅ 완료: {updated}건 분류, {len(keyword_rows)}개 키워드 저장")
    return updated


if __name__ == "__main__":
    run_sentiment()
