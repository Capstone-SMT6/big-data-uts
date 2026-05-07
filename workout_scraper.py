import os
import json
import time
import requests
from datetime import datetime, timedelta
from pymongo import MongoClient  # pyrefly: ignore [missing-import]

# INIT
FITNESS_ARTICLES = [
    # General Fitness & Training
    "Bodybuilding", "Physical_fitness", "Weight_training", "Strength_training", "Aerobic_exercise",
    "Calisthenics", "CrossFit", "High-intensity_interval_training", "Powerlifting", "Olympic_weightlifting",
    "Gymnastics", "Yoga", "Pilates", "Martial_arts", "Running", "Cycling", "Swimming_(sport)",
    # Equipment
    "Dumbbell", "Barbell", "Kettlebell", "Treadmill", "Stationary_bicycle", "Rowing_machine",
    # Nutrition & Supplements
    "Protein_(nutrient)", "Whey_protein", "Creatine", "Branched-chain_amino_acid", "Dietary_supplement",
    "Nutrition", "Ketogenic_diet", "Intermittent_fasting", "Veganism", "Low-carbohydrate_diet",
    # Physiology & Biology
    "Muscle_hypertrophy", "Weight_loss", "Metabolism", "Adipose_tissue", "Heart_rate", "VO2_max",
    "Testosterone", "Human_growth_hormone", "Cortisol",
    # Specific Exercises
    "Squat_(exercise)", "Deadlift", "Bench_press", "Pull-up_(exercise)", "Push-up"
]

HEADERS = {"User-Agent": "FitnessResearchBot_BigDataProject/1.0 (academic research)"}
MONGODB_URI = os.environ.get("MONGODB_URI")
OUTPUT_FILE = "wiki_trends.json"
# END INIT

# DB SETUP
def get_collection():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    return client["big_data_class"]["wiki_trends"]
# END DB SETUP

# WIKI SCRAPER
def scrape_pageviews():
    # 5 years of daily data
    end = datetime.now()
    start = end - timedelta(days=365 * 5)
    start_str = start.strftime("%Y%m%d")
    end_str = end.strftime("%Y%m%d")

    results = {}
    total_data_points = 0
    
    print(f"Fetching daily data from {start_str} to {end_str}...")

    for article in FITNESS_ARTICLES:
        url = (
            f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
            f"/en.wikipedia/all-access/all-agents/{article}/daily/{start_str}/{end_str}"
        )
        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    # Store daily views
                    results[article] = [
                        {
                            "date": item["timestamp"][:4] + "-" + item["timestamp"][4:6] + "-" + item["timestamp"][6:8],
                            "views": item["views"]
                        }
                        for item in items
                    ]
                    points = len(items)
                    total_data_points += points
                    print(f"  [OK] {article}: {points} days")
                    break  # Success, exit retry loop
                elif resp.status_code == 429:
                    print(f"  [WAIT] {article}: HTTP 429 Too Many Requests. Waiting 5s... ({attempt+1}/{max_retries})")
                    time.sleep(5)
                else:
                    print(f"  [FAIL] {article}: HTTP {resp.status_code}")
                    results[article] = []
                    break  # Unrecoverable error, exit retry loop
            except Exception as e:
                print(f"  [ERROR] {article}: {e}")
                if attempt == max_retries - 1:
                    results[article] = []
                time.sleep(5)
        else:
            # If loop completes without break (all retries failed)
            if not results.get(article):
                results[article] = []

        time.sleep(1.0)  # Be polite to Wikipedia's API
        
    print(f"\nTotal data points collected: {total_data_points:,}")
    return results
# END WIKI SCRAPER

# MAIN
def main():
    print(f"Initiating Big Data Wikipedia Scraper ({len(FITNESS_ARTICLES)} Articles)...")
    data = scrape_pageviews()

    doc = {
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "articles": FITNESS_ARTICLES,
        "data": data,
        "metadata": {
            "resolution": "daily",
            "years": 5
        }
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=4)
    print(f"Saved {os.path.getsize(OUTPUT_FILE) / (1024*1024):.2f} MB to {OUTPUT_FILE}")

    if MONGODB_URI:
        try:
            get_collection().insert_one(doc)
            print("Inserted into MongoDB.")
        except Exception as e:
            print(f"MongoDB error (data saved locally): {e}")
    else:
        print("No MONGODB_URI set, skipping MongoDB.")

if __name__ == "__main__":
    main()
# END MAIN
