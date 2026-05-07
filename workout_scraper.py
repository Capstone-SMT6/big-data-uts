import os
import requests
from datetime import datetime
from pymongo import MongoClient

# INIT
SUBREDDITS = ["Fitness", "bodybuilding", "Gym"]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
BASE_URL = "https://arctic-shift.photon-reddit.com/api/posts/search"
LIMIT = 100
MONGODB_URI = os.environ.get("MONGODB_URI", "")
# END INIT

# DB SETUP
def get_collection():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    return client["big_data_class"]["arctic_trends"]
# END DB SETUP

# ARCTIC SHIFT SCRAPER
def scrape_reddit():
    data = []
    for sub in SUBREDDITS:
        print(f"Scraping r/{sub} via Arctic Shift...")
        after = None
        page = 0
        while True:
            params = {"subreddit": sub, "limit": LIMIT, "sort": "desc"}
            if after:
                params["before"] = after
            try:
                response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
                if response.status_code == 200:
                    posts = response.json().get("data", [])
                    if not posts:
                        break
                    page += 1
                    print(f"  Page {page}: got {len(posts)} posts")
                    for p in posts:
                        data.append({
                            "post_id": p.get("id"),
                            "subreddit": sub,
                            "title": p.get("title"),
                            "text": p.get("selftext", ""),
                            "upvotes": p.get("score"),
                            "num_comments": p.get("num_comments"),
                            "created_utc": datetime.fromtimestamp(int(p.get("created_utc", 0)), tz=datetime.now().astimezone().tzinfo).strftime("%Y-%m-%d %H:%M:%S"),
                            "url": p.get("url"),
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    after = posts[-1].get("created_utc")
                else:
                    print(f"  HTTP {response.status_code} for r/{sub}")
                    break
            except Exception as e:
                print(f"Error scraping r/{sub}: {e}")
                break
    return data
# END ARCTIC SHIFT SCRAPER

# MAIN
def main():
    collection = get_collection()
    new_posts = scrape_reddit()

    inserted = 0
    for post in new_posts:
        if not collection.find_one({"post_id": post["post_id"]}):
            collection.insert_one(post)
            inserted += 1

    print(f"Inserted {inserted} new posts into MongoDB (arctic_trends collection).")

if __name__ == "__main__":
    main()
# END MAIN
