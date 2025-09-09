# crawler_test.py  — tiny end-to-end test
import os, re, sys, time, json, random, sqlite3, csv
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ---------- Test config (small, safe) ----------
BASE = "https://forum.charltonlife.com"
INDEX_START = f"{BASE}/discussions"
MIN_YEAR = 2015
LIKE_MIN = 10
LOL_MIN  = 10

THROTTLE_MIN = 6
THROTTLE_MAX = 9
EXTRA_THREAD_PAUSE = 2
DAILY_PAGE_CAP = 30

REFRESH_TOP_N_PAGES = 1
REFRESH_EVERY_N_THREADS = 2
THREAD_BAIL_AFTER_OLD_PAGES = 1

DB_PATH = "charltonlife_test.sqlite"
UA = "Mozilla/5.0 (charltonlife test crawler; contact user)"
TIMEOUT = 40
TEST_INDEX_PAGE_LIMIT = 2
# ----------------------------------------------

def load_cookie():
    env_path = os.path.join(os.path.dirname(__file__), "cookieholder.env")
    load_dotenv(env_path)
    name = os.getenv("CL_COOKIE_NAME")
    value = os.getenv("CL_COOKIE_VALUE")
    if not name or not value:
        print("Missing CL_COOKIE_NAME or CL_COOKIE_VALUE in cookieholder.env")
        sys.exit(1)
    return {name: value}

COOKIES = load_cookie()
HEADERS = {"User-Agent": UA}

def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS threads(
        discussion_id INTEGER PRIMARY KEY,
        url TEXT NOT NULL,
        title TEXT,
        last_activity_dt TEXT,
        page_count INTEGER,
        scanned_page INTEGER DEFAULT 0,
        status TEXT DEFAULT 'queued',
        first_seen_dt TEXT
    );
    CREATE TABLE IF NOT EXISTS posts(
        post_id INTEGER PRIMARY KEY,
        discussion_id INTEGER,
        url TEXT,
        author TEXT,
        posted_at TEXT,
        likes INTEGER,
        lols INTEGER
    );
    """)
    conn.commit()

def upsert_thread(conn, t):
    conn.execute("""
    INSERT INTO threads(discussion_id,url,title,last_activity_dt,page_count,scanned_page,status,first_seen_dt)
    VALUES(?,?,?,?,?,?,?,?)
    ON CONFLICT(discussion_id) DO UPDATE SET
      url=excluded.url,
      title=COALESCE(excluded.title,threads.title),
      last_activity_dt=COALESCE(excluded.last_activity_dt,threads.last_activity_dt),
      page_count=COALESCE(excluded.page_count,threads.page_count),
      first_seen_dt=COALESCE(threads.first_seen_dt,excluded.first_seen_dt)
    """, (t["discussion_id"], t["url"], t.get("title"), t.get("last_activity_dt"),
          t.get("page_count"), t.get("scanned_page",0), t.get("status","queued"), t.get("first_seen_dt")))
    conn.commit()

def set_thread_progress(conn, did, scanned_page=None, page_count=None, status=None):
    fields, vals = [], []
    if scanned_page is not None: fields += ["scanned_page=?" ] ; vals += [scanned_page]
    if page_count  is not None: fields += ["page_count=?"] ; vals += [page_count]
    if status      is not None: fields += ["status=?"]     ; vals += [status]
    if not fields: return
    vals.append(did)
    conn.execute(f"UPDATE threads SET {', '.join(fields)} WHERE discussion_id=?", vals)
    conn.commit()

def insert_posts(conn, rows):
    if not rows: return
    conn.executemany("""
    INSERT OR IGNORE INTO posts(post_id,discussion_id,url,author,posted_at,likes,lols)
    VALUES(?,?,?,?,?,?,?)
    """, rows)
    conn.commit()

def next_queued_threads(conn, limit=20):
    return conn.execute(f"""
        SELECT discussion_id, url, COALESCE(page_count,1), scanned_page
        FROM threads
        WHERE status='queued'
        ORDER BY COALESCE(page_count,1) DESC, last_activity_dt DESC
        LIMIT {limit}
    """).fetchall()

def throttle(extra=0):
    t = random.uniform(THROTTLE_MIN, THROTTLE_MAX) + extra
    time.sleep(t)

def parse_iso(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z","")).replace(tzinfo=timezone.utc)
    except Exception:
        return None

CUTOFF_DT = datetime(MIN_YEAR,1,1,tzinfo=timezone.utc)

def is_cf_interstitial(text):
    return ("cf-browser-verification" in text) or ("cf-please-wait" in text) or ("cf_chl_" in text)

pages_fetched_today = 0
day_start_epoch = int(time.time())

def reset_daily_if_needed():
    global pages_fetched_today, day_start_epoch
    now = int(time.time())
    if now - day_start_epoch >= 86400:
        day_start_epoch = now
        pages_fetched_today = 0

def fetch(url):
    global pages_fetched_today
    reset_daily_if_needed()
    if pages_fetched_today >= DAILY_PAGE_CAP:
        print(f"[CAP] Reached daily cap {DAILY_PAGE_CAP}. Exiting test.")
        sys.exit(0)
    try:
        r = requests.get(url, headers={"User-Agent": UA}, cookies=COOKIES, timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"[ERR] Request failed: {e}")
        time.sleep(30)
        raise
    if r.status_code in (429,403,503) or is_cf_interstitial(r.text):
        print(f"[WARN] {r.status_code} or Cloudflare at {url}. Exiting test.")
        sys.exit(0)
    pages_fetched_today += 1
    return r

def extract_discussions_from_index(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for a in soup.select("a.Title, a.DiscussionLink"):
        href = a.get("href") or ""
        if "/discussion/" not in href: continue
        full = urljoin(BASE, href.split("#")[0])
        m = re.search(r"/discussion/(\d+)", full)
        if not m: continue
        did = int(m.group(1))
        title = a.get_text(strip=True)
        parent = a.find_parent(["li","div"])
        last_dt = None
        if parent:
            t = parent.select_one("time[datetime], abbr.TimeStamp")
            if t and t.has_attr("datetime"):
                last_dt = t["datetime"]
        items.append({"discussion_id": did, "url": full, "title": title, "last_activity_dt": last_dt})
    # dedupe
    seen, out = set(), []
    for it in items:
        if it["discussion_id"] in seen: continue
        seen.add(it["discussion_id"]); out.append(it)
    return out

def thread_last_page(soup):
    nums = []
    for a in soup.select(".Pager a, .Pagination a"):
        txt = a.get_text(strip=True)
        if txt.isdigit(): nums.append(int(txt))
    return max(nums) if nums else 1

def extract_posts_from_thread(html, base_url, did):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    posts = soup.select('li[id^="Comment_"]')
    all_old = True
    for li in posts:
        m = re.search(r"Comment_(\d+)", li.get("id",""))
        if not m: continue
        pid = int(m.group(1))
        perma = li.select_one("a.Permalink")
        link = urljoin(base_url, perma["href"]) if perma and perma.has_attr("href") else base_url
        author_el = li.select_one(".Username")
        author = author_el.get_text(strip=True) if author_el else "Unknown"
        t = li.select_one("time[datetime]")
        posted_at = t["datetime"] if t and t.has_attr("datetime") else (t.get_text(strip=True) if t else "")
        dt_obj = parse_iso(posted_at) if posted_at else None
        if dt_obj and dt_obj >= CUTOFF_DT:
            all_old = False
        like_el = li.select_one("a.ReactButton-Like .Count")
        lol_el  = li.select_one("a.ReactButton-LOL .Count")
        likes = int(like_el.get_text(strip=True)) if like_el and like_el.get_text(strip=True).isdigit() else 0
        lols  = int(lol_el.get_text(strip=True)) if lol_el and lol_el.get_text(strip=True).isdigit() else 0
        if dt_obj and dt_obj >= CUTOFF_DT and (likes >= LIKE_MIN or lols >= LOL_MIN):
            rows.append((pid, did, link, author, dt_obj.isoformat(), likes, lols))
    return rows, all_old, soup

def page_url_for(thread_url, page_num):
    if page_num == 1: return thread_url
    return f"{thread_url}/p{page_num}"

def index_page_url(page_num):
    if page_num == 1: return INDEX_START
    return f"{INDEX_START}/p{page_num}"

def collect_index_test(conn):
    page = 1
    total_new = 0
    while True:
        url = index_page_url(page)
        print(f"[Index] {url}")
        r = fetch(url)
        if r.status_code != 200:
            print(f"[Index] HTTP {r.status_code}, stop."); break
        items = extract_discussions_from_index(r.text)
        if not items:
            print("[Index] No threads found, stop."); break
        new_this = 0
        for it in items:
            it["first_seen_dt"] = datetime.now(timezone.utc).isoformat()
            exists = conn.execute("SELECT 1 FROM threads WHERE discussion_id=?", (it["discussion_id"],)).fetchone()
            upsert_thread(conn, it)
            if not exists: new_this += 1; total_new += 1
        print(f"[Index] Page {page}: +{new_this} new")
        page += 1
        throttle()
        if page > TEST_INDEX_PAGE_LIMIT:
            print("[Index] Test mode: stopping after 2 pages.")
            break
    print(f"[Index] Test pass complete. New threads: {total_new}")

def refresh_top_index(conn):
    print("[Index] Refreshing top page...")
    for p in range(1, REFRESH_TOP_N_PAGES + 1):
        url = index_page_url(p)
        r = fetch(url)
        if r.status_code != 200:
            print(f"[Index] Refresh HTTP {r.status_code} {url}"); break
        items = extract_discussions_from_index(r.text)
        for it in items:
            it["first_seen_dt"] = datetime.now(timezone.utc).isoformat()
            upsert_thread(conn, it)
        throttle()

def scan_thread(conn, did, url, start_page=1):
    print(f"[Thread] {did} p{start_page}")
    r = fetch(page_url_for(url, start_page))
    if r.status_code != 200:
        print(f"[Thread] HTTP {r.status_code} {url}")
        set_thread_progress(conn, did, status="error"); return
    rows, all_old, soup = extract_posts_from_thread(r.text, url, did)
    last_page = thread_last_page(soup)
    insert_posts(conn, rows)
    set_thread_progress(conn, did, scanned_page=start_page, page_count=last_page, status="running")
    throttle(EXTRA_THREAD_PAUSE)

    consecutive_old = 1 if all_old else 0
    for p in range(start_page + 1, last_page + 1):
        page_url = page_url_for(url, p)
        r = fetch(page_url)
        if r.status_code != 200:
            print(f"[Thread] HTTP {r.status_code} {page_url}")
            set_thread_progress(conn, did, scanned_page=p, status="error"); return
        rows, all_old, _ = extract_posts_from_thread(r.text, url, did)
        insert_posts(conn, rows)
        set_thread_progress(conn, did, scanned_page=p, status="running")
        consecutive_old = consecutive_old + 1 if all_old else 0
        if consecutive_old >= THREAD_BAIL_AFTER_OLD_PAGES:
            print(f"[Thread] {did} early-stop after {consecutive_old} old page(s).")
            break
        throttle(EXTRA_THREAD_PAUSE)

    set_thread_progress(conn, did, status="done")
    print(f"[Thread] {did} done.")

def export_top_lists(conn):
    cutoff_iso = datetime(MIN_YEAR,1,1,tzinfo=timezone.utc).isoformat()
    def write_csv(path, rows):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rank","post_id","author","posted_at","url","likes","lols"])
            for i, r in enumerate(rows, start=1):
                w.writerow([i] + list(r))

    rows = conn.execute(f"""
        SELECT post_id, author, posted_at, url, likes, lols
        FROM posts
        WHERE posted_at >= ? AND (likes >= ? OR lols >= ?)
        ORDER BY likes DESC, (likes + lols) DESC, posted_at DESC
        LIMIT 20
    """, (cutoff_iso, LIKE_MIN, LOL_MIN)).fetchall()
    write_csv("test_top20_likes.csv", rows)

    rows = conn.execute(f"""
        SELECT post_id, author, posted_at, url, likes, lols
        FROM posts
        WHERE posted_at >= ? AND (likes >= ? OR lols >= ?)
        ORDER BY lols DESC, (likes + lols) DESC, posted_at DESC
        LIMIT 20
    """, (cutoff_iso, LIKE_MIN, LOL_MIN)).fetchall()
    write_csv("test_top20_lols.csv", rows)

    rows = conn.execute(f"""
        SELECT post_id, author, posted_at, url, likes, lols
        FROM posts
        WHERE posted_at >= ? AND (likes >= ? OR lols >= ?)
        ORDER BY (likes + lols) DESC, posted_at DESC
        LIMIT 20
    """, (cutoff_iso, LIKE_MIN, LOL_MIN)).fetchall()
    write_csv("test_top20_combined.csv", rows)

    print("Exported: test_top20_likes.csv, test_top20_lols.csv, test_top20_combined.csv")

def main():
    conn = db_conn()
    init_db(conn)

    collect_index_test(conn)

    threads_done = 0
    while True:
        q = next_queued_threads(conn, limit=10)
        if not q:
            refresh_top_index(conn)
            q = next_queued_threads(conn, limit=10)
            if not q:
                print("[Main] No queued threads left in test.")
                break
        for did, url, page_count, scanned in q:
            scan_thread(conn, did, url, start_page=max(1, scanned or 1))
            threads_done += 1
            if threads_done % REFRESH_EVERY_N_THREADS == 0:
                refresh_top_index(conn)

    export_top_lists(conn)
    conn.close()

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print("Fatal error:", e)
        sys.exit(1)