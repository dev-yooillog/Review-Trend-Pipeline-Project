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
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://shopping.naver.com",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

SEARCH_TARGETS = [
    {"category": "공기청정기", "query": "공기청정기"},
    {"category": "로봇청소기", "query": "로봇청소기"},
    {"category": "건조기",    "query": "의류건조기"},
]

def search_products(query: str, display: int = 10) -> list[dict]:
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {
        **HEADERS,
        "X-Naver-Client-Id":     NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": query, "display": display, "sort": "sim"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception as e:
        print(f" API 오류 ({query}): {e}")
        return []

    products = []
    for item in items:
        pid = hashlib.md5(item.get("productId", item["title"]).encode()).hexdigest()[:12]
        products.append({
            "product_id": pid,
            "brand":      item.get("brand") or "기타",
            "name":       BeautifulSoup(item["title"], "html.parser").get_text(),
            "price":      int(item.get("lprice", 0)),
        })
    return products

def crawl_reviews(product_id: str, product_name: str, max_pages: int = 5) -> list[dict]:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    reviews = []

    try:
        for page in range(1, max_pages + 1):
            url = (
                f"https://search.shopping.naver.com/product/{product_id}/review"
                f"?page={page}&sort=recent"
            )
            driver.get(url)
            time.sleep(random.uniform(2.0, 3.5))

            soup = BeautifulSoup(driver.page_source, "html.parser")
            review_els = soup.select("li.ReviewItem__reviewItem___1w7g5")

            if not review_els:
                print(f"  {product_name} - {page}p 리뷰 없음, 중단")
                break

            for el in review_els:
                star_el = el.select_one(".ReviewItem__grade___2A9a5")
                text_el = el.select_one(".ReviewItem__reviewContent___3v5AA")
                date_el = el.select_one(".ReviewItem__date___1Yoqy")
                help_el = el.select_one(".ReviewItem__helpfulCount___2VnQQ")

                text = text_el.get_text(strip=True) if text_el else ""
                if not text:
                    continue

                date_str = date_el.get_text(strip=True) if date_el else ""
                rid = hashlib.md5(f"{product_id}{text}{date_str}".encode()).hexdigest()[:16]

                reviews.append({
                    "review_id":   rid,
                    "product_id":  product_id,
                    "star_rating": int(star_el.get_text(strip=True)) if star_el else 0,
                    "review_text": text,
                    "review_date": date_str,
                    "helpful_cnt": int(help_el.get_text(strip=True).replace(",", "")) if help_el else 0,
                })

            print(f"  {product_name} - {page}p: {len(review_els)}건")

    finally:
        driver.quit()

    return reviews

def save_products(products: list[dict], category: str):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    for p in products:
        cur.execute("""
            INSERT OR IGNORE INTO products (product_id, brand, name, category, price)
            VALUES (:product_id, :brand, :name, :category, :price)
        """, {**p, "category": category})
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
            print(f"  오류: {e}")
    conn.commit()
    conn.close()
    return new_count

def main():
    init_db()
    total_new = 0

    for target in SEARCH_TARGETS:
        category = target["category"]
        query    = target["query"]

        products = search_products(query, display=5)
        if not products:
            print(f"  제품을 찾지 못함.")
            continue

        save_products(products, category)
        print(f"  제품 {len(products)}개 저장")

        for p in products:
            print(f"\n  {p['name'][:30]}... 리뷰 수집 중")
            reviews = crawl_reviews(p["product_id"], p["name"], max_pages=3)
            new_cnt = save_reviews(reviews)
            total_new += new_cnt
            print(f"  신규 {new_cnt}건 저장 (전체 {len(reviews)}건 수집)")

    print(f"\n 총 신규 리뷰 {total_new}건 저장")
    return total_new

if __name__ == "__main__":
    main()