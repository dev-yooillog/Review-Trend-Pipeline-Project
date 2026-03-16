import sqlite3

DB_PATH = "reviews.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            product_id   TEXT PRIMARY KEY,
            brand        TEXT,
            name         TEXT,
            category     TEXT,
            price        INTEGER,
            created_at   TEXT DEFAULT (DATE('now'))
        );

        CREATE TABLE IF NOT EXISTS reviews (
            review_id    TEXT PRIMARY KEY,
            product_id   TEXT REFERENCES products(product_id),
            star_rating  INTEGER,
            review_text  TEXT,
            sentiment    TEXT,
            review_date  TEXT,
            helpful_cnt  INTEGER DEFAULT 0,
            collected_at TEXT DEFAULT (DATETIME('now'))
        );

        CREATE TABLE IF NOT EXISTS keywords (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id    TEXT REFERENCES reviews(review_id),
            keyword      TEXT,
            frequency    INTEGER DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_date    ON reviews(review_date);
        CREATE INDEX IF NOT EXISTS idx_keywords_review ON keywords(review_id);
    """)
    conn.commit()
    conn.close()
    print("✅ DB 초기화 완료")

if __name__ == "__main__":
    init_db()
