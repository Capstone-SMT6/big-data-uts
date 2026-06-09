import os
import json
import time
import requests
from datetime import datetime, timedelta
from collections import deque
import urllib.parse
from pymongo import MongoClient

FITNESS_ARTICLES = [
    "Push-up", "Sit-up", "Crunch_(exercise)", "Plank_(exercise)", "Squat_(exercise)",
    "Calisthenics", "Bodyweight_exercise", "Physical_fitness", "Strength_training",
    "Aerobic_exercise", "High-intensity_interval_training", "Stretching", "Warm_up",
    "Weight_loss", "Muscle_hypertrophy", "Physical_exercise",
    "Basal_metabolic_rate", "Body_mass_index", "Heart_rate"
]

HEADERS = {"User-Agent": "SmaFitResearchBot/1.0 (panjirafi96@gmail.com; academic research)"}
MONGODB_URI = os.environ.get("MONGODB_URI")
OUTPUT_FILE = "wiki_trends.json"

def get_collection():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    return client["big_data_class"]["wiki_trends"]

def scrape_pageviews():
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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
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
                    break
                elif resp.status_code == 429:
                    print(f"  [WAIT] {article}: HTTP 429 Too Many Requests. Waiting 15s... ({attempt+1}/{max_retries})")
                    time.sleep(15)
                else:
                    print(f"  [FAIL] {article}: HTTP {resp.status_code}")
                    results[article] = []
                    break
            except Exception as e:
                print(f"  [ERROR] {article}: {e}")
                if attempt == max_retries - 1:
                    results[article] = []
                time.sleep(15)
        else:
            if not results.get(article):
                results[article] = []

        time.sleep(2.0)
        
    print(f"\nTotal data points collected: {total_data_points:,}")
    return results

def translate_to_indonesian(text):
    if not text:
        return ""
    encoded_text = urllib.parse.quote(text)
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=id&dt=t&q={encoded_text}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            translated_chunks = []
            if data and data[0]:
                for chunk in data[0]:
                    if chunk and chunk[0]:
                        translated_chunks.append(chunk[0])
                return "".join(translated_chunks)
    except Exception as e:
        print(f"  [ERROR translate]: {e}")
    return text

def get_indonesian_summary(article):
    langlinks_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=langlinks&titles={article}&lllang=id&format=json"
    id_title = None
    try:
        resp = requests.get(langlinks_url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                langlinks = page_data.get("langlinks", [])
                if langlinks:
                    id_title = langlinks[0].get("*")
        elif resp.status_code == 429:
            return None 
    except Exception as e:
        print(f"  [ERROR langlink] {article}: {e}")
        return None 

    desc = ""
    if id_title:
        print(f"  [LOG] Found Indonesian title for '{article}': '{id_title}'")
        summary_url = f"https://id.wikipedia.org/api/rest_v1/page/summary/{id_title}"
        try:
            resp = requests.get(summary_url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                desc = data.get("description", "") or data.get("extract", "")
                if desc and len(desc) > 150:
                    desc = desc[:147] + "..."
            elif resp.status_code == 429:
                return None
        except Exception as e:
            print(f"  [ERROR ID summary] {id_title}: {e}")
            return None
    else:
        print(f"  [LOG] No Indonesian title found for '{article}'")

    if not desc.strip():
        print(f"  [LOG] No Indonesian description available for '{article}', fetching English summary...")
        en_summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{article}"
        try:
            resp = requests.get(en_summary_url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                en_desc = data.get("description", "") or data.get("extract", "")
                if en_desc:
                    print(f"  [LOG] Translating English description of '{article}' to Indonesian...")
                    desc = translate_to_indonesian(en_desc)
                    if desc and len(desc) > 150:
                        desc = desc[:147] + "..."
            elif resp.status_code == 429:
                return None
        except Exception as e:
            print(f"  [ERROR EN summary] {article}: {e}")
            return None

    return desc

def scrape_descriptions(articles):
    descriptions = {}
    
    existing_descriptions = {}
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old_doc = json.load(f)
            existing_descriptions = old_doc.get("descriptions", {})
    except Exception:
        pass

    print("\nFetching article descriptions dynamically in Indonesian...")
    
    queue = deque()
    for article in articles:
        if article in existing_descriptions and existing_descriptions[article].strip():
            descriptions[article] = existing_descriptions[article]
            print(f"  [OK - Cached] Summary for {article} (ID)")
        else:
            queue.append(article)
            
    retry_counts = {article: 0 for article in queue}
    max_retries = 3
    
    while queue:
        article = queue.popleft()
        desc = get_indonesian_summary(article)
        
        if desc is not None:
            descriptions[article] = desc
            if desc:
                print(f"  [OK] Summary for {article} (ID): {desc[:45]}...")
            else:
                print(f"  [OK - empty] No summary available for {article}")
            time.sleep(1.5)
        else:
            retry_counts[article] += 1
            if retry_counts[article] <= max_retries:
                print(f"  [RETRY QUEUE] Failed to fetch {article}, moving to end of queue... (Attempt {retry_counts[article]}/{max_retries})")
                queue.append(article)
                time.sleep(3.0)
            else:
                descriptions[article] = ""
                print(f"  [FAIL] Summary for {article} (ID): Failed after {max_retries} retries")
                time.sleep(1.0)
                
    return descriptions

def main():
    print(f"Initiating Big Data Wikipedia Scraper ({len(FITNESS_ARTICLES)} Articles)...")
    data = scrape_pageviews()
    descriptions = scrape_descriptions(FITNESS_ARTICLES)

    doc = {
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "articles": FITNESS_ARTICLES,
        "data": data,
        "descriptions": descriptions,
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