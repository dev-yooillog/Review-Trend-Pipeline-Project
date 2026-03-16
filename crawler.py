import os
import time
import random
import hashlib
import sqlite3
import requests
from bs4 import BeautifulSoup
from db_setup import init_db, DB_PATH

NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Naver-Client-Id":     NAVER_CLIENT_ID,
    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
}

SEARCH_TARGETS = [
    {"category": "공기청정기", "query": "공기청정기 후기"},
    {"category": "로봇청소기", "query": "로봇청소기 후기"},
    {"category": "건조기",    "query": "의류건조기 후기"},
]

def search_blogs(query: str, display: int = 100, start: int = 1) -> list[dict]:
    url = "https://openapi.naver.com/v1/search/blog.json"
    params = {
        "query":   query,
        "display": display,
        "start":   start,
        "sort":    "date",
    }
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("items", [])
    except Exception as e:
        print(f"  API 오류 ({query}): {e}")
        return []

def parse_blog_items(items: list[dict], category: str) -> list[dict]:
    reviews = []
    for item in items:
        title   = BeautifulSoup(item.get("title", ""),       "html.parser").get_text()
        desc    = BeautifulSoup(item.get("description", ""), "html.parser").get_text()
        text    = f"{title} {desc}".strip()
        link    = item.get("link", "")
        date    = item.get("postdate", "")
        blogger = item.get("bloggername", "")

        if not text:
            continue

        rid = hashlib.md5(link.encode()).hexdigest()[:16]
        reviews.append({
            "review_id":   rid,
            "product_id":  category,
            "star_rating": 0,
            "review_text": text,
            "review_date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
            "helpful_cnt": 0,
            "blogger":     blogger,
        })
    return reviews

def save_category_as_product(category: str):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO products (product_id, brand, name, category, price)
        VALUES (?, ?, ?, ?, ?)
    """, (category, "블로그", category, category, 0))
    conn.commit()
    conn.close()

def save_reviews(reviews: list[dict]) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    new_count = 0
    for r in reviews:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO reviews
                    (review_id, product_id, star_rating, review_text, review_date, helpful_cnt)
                VALUES
                    (:review_id, :product_id, :star_rating, :review_text, :review_date, :helpful_cnt)
            """, r)
            if cur.rowcount:
                new_count += 1
        except Exception as e:
            print(f"  저장 오류: {e}")
    conn.commit()
    conn.close()
    return new_count

def main():
    init_db()
    total_new = 0

    for target in SEARCH_TARGETS:
        category = target["category"]
        query    = target["query"]
        print(f"\n  [{category}] 블로그 수집 중...")

        save_category_as_product(category)

        all_items = []
        for start in range(1, 201, 100):   # 100건씩 2회 = 최대 200건
            items = search_blogs(query, display=100, start=start)
            if not items:
                break
            all_items.extend(items)
            time.sleep(random.uniform(0.5, 1.0))

        reviews = parse_blog_items(all_items, category)
        new_cnt = save_reviews(reviews)
        total_new += new_cnt
        print(f"  수집 {len(reviews)}건 / 신규 저장 {new_cnt}건")

    print(f"\n완료! 총 신규 {total_new}건 저장")
    return total_new

if __name__ == "__main__":
    main()