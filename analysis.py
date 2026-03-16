import sqlite3
import pandas as pd
from db_setup import DB_PATH


def get_conn():
    return sqlite3.connect(DB_PATH)


# ── 1. 카테고리별 평균 별점 트렌드 ───────────────────────────────────
def avg_star_by_category():
    query = """
        SELECT
            p.category,
            SUBSTR(r.review_date, 1, 7) AS year_month,
            ROUND(AVG(r.star_rating), 2) AS avg_star,
            COUNT(*)                     AS review_cnt
        FROM reviews r
        JOIN products p ON r.product_id = p.product_id
        WHERE r.review_date IS NOT NULL
        GROUP BY p.category, year_month
        ORDER BY p.category, year_month
    """
    df = pd.read_sql(query, get_conn())
    print("카테고리별 평균 별점 트렌드")
    print(df.to_string(index=False))
    return df


# ── 2. 브랜드별 감성 비율 ─────────────────────────────────────────────
def sentiment_by_brand():
    query = """
        SELECT
            p.brand,
            r.sentiment,
            COUNT(*) AS cnt,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY p.brand), 1) AS pct
        FROM reviews r
        JOIN products p ON r.product_id = p.product_id
        WHERE r.sentiment IS NOT NULL
        GROUP BY p.brand, r.sentiment
        ORDER BY p.brand, r.sentiment
    """
    df = pd.read_sql(query, get_conn())
    print("\n브랜드별 감성 비율")
    print(df.to_string(index=False))
    return df


# ── 3. 부정 리뷰 상위 키워드 ─────────────────────────────────────────
def top_negative_keywords(top_n: int = 20):
    query = """
        SELECT
            k.keyword,
            COUNT(*) AS freq
        FROM keywords k
        JOIN reviews r ON k.review_id = r.review_id
        WHERE r.sentiment = 'negative'
          AND LENGTH(k.keyword) >= 2
        GROUP BY k.keyword
        ORDER BY freq DESC
        LIMIT :top_n
    """
    df = pd.read_sql(query, get_conn(), params={"top_n": top_n})
    print(f"\n부정 리뷰 상위 키워드 Top {top_n}")
    print(df.to_string(index=False))
    return df


# ── 4. 주간 리뷰 수집량 모니터링 ─────────────────────────────────────
def weekly_collection_summary():
    query = """
        SELECT
            STRFTIME('%Y-W%W', collected_at) AS week,
            COUNT(*)                          AS collected,
            ROUND(AVG(star_rating), 2)        AS avg_star
        FROM reviews
        GROUP BY week
        ORDER BY week DESC
        LIMIT 8
    """
    df = pd.read_sql(query, get_conn())
    print("\n주간 수집량 요약")
    print(df.to_string(index=False))
    return df


# ── 5. 이슈 키워드 급등 감지 ─────────────────────────────────────────
ISSUE_KEYWORDS = ["고장", "AS", "환불", "반품", "소음", "불량", "오류"]

def detect_issue_spike():
    conn = get_conn()
    results = []

    for kw in ISSUE_KEYWORDS:
        query = """
            SELECT
                SUBSTR(r.review_date, 1, 7) AS ym,
                COUNT(*) AS cnt
            FROM keywords k
            JOIN reviews r ON k.review_id = r.review_id
            WHERE k.keyword LIKE :kw
            GROUP BY ym
            ORDER BY ym DESC
            LIMIT 3
        """
        df = pd.read_sql(query, conn, params={"kw": f"%{kw}%"})
        if len(df) >= 2:
            latest = df.iloc[0]["cnt"]
            prev   = df.iloc[1]["cnt"]
            if prev > 0 and latest / prev >= 1.5:
                results.append({
                    "keyword":  kw,
                    "latest":   latest,
                    "prev":     prev,
                    "increase": f"+{round((latest/prev - 1)*100)}%"
                })

    conn.close()
    if results:
        print("\n이슈 키워드 급등 발견함")
        for r in results:
            print(f"  [{r['keyword']}] {r['prev']} → {r['latest']} ({r['increase']})")
    else:
        print("\n이슈 급등 없음")

    return results


# ── 6. Tableau용 데이터 CSV 내보내기 ─────────────────────────────────
def export_for_tableau():
    queries = {
        "tableau_reviews.csv": """
            SELECT
                r.review_id, r.star_rating, r.sentiment,
                r.review_date, r.helpful_cnt,
                p.brand, p.name AS product_name, p.category, p.price
            FROM reviews r
            JOIN products p ON r.product_id = p.product_id
        """,
        "tableau_keywords.csv": """
            SELECT
                k.keyword, k.frequency,
                r.sentiment, r.review_date,
                p.brand, p.category
            FROM keywords k
            JOIN reviews r ON k.review_id = r.review_id
            JOIN products p ON r.product_id = p.product_id
        """,
    }
    conn = get_conn()
    for filename, query in queries.items():
        df = pd.read_sql(query, conn)
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"{filename} 저장 ({len(df):,}행)")
    conn.close()


if __name__ == "__main__":
    avg_star_by_category()
    sentiment_by_brand()
    top_negative_keywords()
    weekly_collection_summary()
    detect_issue_spike()
    export_for_tableau()
