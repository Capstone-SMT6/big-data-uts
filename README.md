# 🏋️‍♂️ Workout Trend Scraper

A robust, automated data collection pipeline designed for academic research to track search interest and trends in various fitness and workout topics over time. This project was built for the Big Data class (UTS).

It retrieves **5 years of daily English Wikipedia pageviews** for 19 key fitness articles, fetches or translates their **Indonesian summaries**, and stores the aggregated datasets both locally and directly into a **MongoDB database**.

---

## ✨ Features

- **📅 5-Year History Tracking**: Fetches daily pageview data points spanning the last 5 years via the Wikimedia REST API.
- **🇮🇩 Auto-Translation & Localization**: 
  - Searches for equivalent Indonesian Wikipedia articles first.
  - Dynamically translates English abstracts to Indonesian using Google Translate API if no Indonesian equivalent is found.
  - Smart caching to avoid redundant API queries.
- **☁️ MongoDB Integration**: Securely uploads scraped data directly to MongoDB Atlas.
- **🤖 Fully Automated Schedule**: Nightly automation run using GitHub Actions (runs every day at `00:00 WIB` / `17:00 UTC`).

---

## 🛠️ Tech Stack & Dependencies

- **Language**: Python 3.11
- **Storage**: MongoDB & Local JSON Cache
- **Libraries**:
  - `requests` (API Requests)
  - `pymongo` (MongoDB Client)
  - `pytrends` & `matplotlib` (Analysis & Visualization)

---

## 🚀 Getting Started

### 1. Prerequisites
Make sure you have Python 3.11 installed.

### 2. Install Dependencies
Install all required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables
To enable database storage, set the `MONGODB_URI` environment variable:

- **Windows (CMD)**:
  ```cmd
  set MONGODB_URI="your_mongodb_connection_string"
  ```
- **Windows (PowerShell)**:
  ```powershell
  $env:MONGODB_URI="your_mongodb_connection_string"
  ```
- **Linux/macOS**:
  ```bash
  export MONGODB_URI="your_mongodb_connection_string"
  ```

*If `MONGODB_URI` is not set, the script will skip database upload and save the output locally in `wiki_trends.json`.*

### 4. Run the Scraper
Run the main script to start collecting pageviews and translations:
```bash
python workout_scraper.py
```

---

## 📁 Project Structure

```
├── .github/
│   └── workflows/
│       └── scraper.yml         # GitHub Actions schedule workflow
├── UTS_Big_Data.ipynb          # Notebook for analysis & visualizations
├── requirements.txt            # Python dependencies
├── workout_scraper.py          # Main scraper script
└── wiki_trends.json            # Locally saved scraped data cache
```

---

## 📊 Data Schema (`wiki_trends.json`)

The final output is formatted as a single JSON object:

```json
{
  "scraped_at": "YYYY-MM-DD HH:MM:SS",
  "articles": [ ... ],
  "data": {
    "Push-up": [
      { "date": "YYYY-MM-DD", "views": 1250 }
    ]
  },
  "descriptions": {
    "Push-up": "Push-up adalah latihan kekuatan umum yang dilakukan dalam posisi tengkurap..."
  },
  "metadata": {
    "resolution": "daily",
    "years": 5
  }
}
```

---

## 🤖 GitHub Actions Workflow

The scraper is configured to run automatically using GitHub Actions (`.github/workflows/scraper.yml`):
- **Triggers**:
  - `schedule`: Daily at `17:00 UTC` (Midnight WIB).
  - `workflow_dispatch`: Can be triggered manually from the "Actions" tab on GitHub.
- **Requirements**: Define `MONGODB_URI` under **Settings > Secrets and variables > Actions** in your GitHub repository.
