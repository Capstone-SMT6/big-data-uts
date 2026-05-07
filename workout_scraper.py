import os
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime
from pymongo import MongoClient

# INIT
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = "big_data_class"
COLLECTION_NAME = "workout_trends"
SUBREDDITS = ["Fitness", "bodybuilding", "Gym"]
HEADERS = {"User-Agent": "workout-trend-scraper/1.0 by u/JustParadis"}
# END INIT

# DB SETUP
def get_db_collection():
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    return db[COLLECTION_NAME]
# END DB SETUP

# REDDIT SCRAPER
def scrape_reddit():
    data = []
    for sub in SUBREDDITS:
        print(f"Scraping r/{sub}...")
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=100"
        try:
            response = requests.get(url, headers=HEADERS, verify=False)
            if response.status_code == 200:
                posts = response.json().get('data', {}).get('children', [])
                for post in posts:
                    p = post['data']
                    data.append({
                        "post_id": p.get("id"),
                        "subreddit": sub,
                        "title": p.get("title"),
                        "text": p.get("selftext", ""),
                        "upvotes": p.get("score"),
                        "num_comments": p.get("num_comments"),
                        "created_utc": datetime.fromtimestamp(p.get("created_utc")),
                        "url": p.get("url"),
                        "scraped_at": datetime.utcnow()
                    })
            else:
                print(f"Failed to fetch r/{sub}: {response.status_code}")
        except Exception as e:
            print(f"Error scraping r/{sub}: {e}")
    return data
# END REDDIT SCRAPER

# MAIN
def main():
    collection = get_db_collection()
    new_posts = scrape_reddit()
    
    if not new_posts:
        print("No new posts found.")
        return

    inserted_count = 0
    for post in new_posts:
        # Check for duplicates before inserting
        if not collection.find_one({"post_id": post["post_id"]}):
            collection.insert_one(post)
            inserted_count += 1
            
    print(f"Inserted {inserted_count} new posts into MongoDB.")

if __name__ == "__main__":
    main()
# END MAIN
