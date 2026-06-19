import os
import json
import time
import requests
from typing import Optional, List
import pandas as pd

# =====================================================================
# 1. KELAS SCRAPER NUTRISI MAKANAN (OPEN FOOD FACTS API)
# =====================================================================

class FoodNutritionScraper:
    """
    Kelas untuk mengelola scraping dan query data nutrisi dari Open Food Facts API.
    """
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.api_url = "https://world.openfoodfacts.org/cgi/search.pl"
        self.headers = {
            "User-Agent": "SmartCoachFitness_Capstone - Python - Version 1.2"
        }
        # Membuat folder output jika belum ada
        os.makedirs(self.output_dir, exist_ok=True)

    def get_nutrition_data(self, food_name: str) -> Optional[dict]:
        """
        Mencari data nutrisi makanan dari Open Food Facts secara teliti dan terstruktur.
        """
        print(f"[INFO] Mencari data nutrisi untuk: '{food_name}'...")
        
        # Parameter pencarian yang aman dan ter-encode otomatis
        params = {
            "search_terms": food_name,
            "search_simple": 1,
            "action": "process",
            "json": 1
        }
        
        try:
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('products') and len(data['products']) > 0:
                # Mengambil produk pertama yang paling relevan
                product = data['products'][0]
                nutriments = product.get('nutriments', {})
                
                # Ekstraksi nutrisi secara rinci
                result = {
                    "query_makanan": food_name,
                    "nama_produk": product.get('product_name', 'Tidak diketahui'),
                    "brand": product.get('brands', 'Tidak diketahui'),
                    "kalori_100g": nutriments.get('energy-kcal_100g', 0),
                    "protein_100g": nutriments.get('proteins_100g', 0),
                    "karbohidrat_100g": nutriments.get('carbohydrates_100g', 0),
                    "lemak_100g": nutriments.get('fat_100g', 0),
                    "serat_100g": nutriments.get('fiber_100g', 0),
                    "sugars_100g": nutriments.get('sugars_100g', 0),
                    "sumber_data": "Open Food Facts API"
                }
                
                print(f"  [SUCCESS] Ditemukan: {result['nama_produk']} | Kalori: {result['kalori_100g']} kcal")
                return result
            else:
                print(f"  [WARN] Makanan '{food_name}' tidak ditemukan di database API.")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] Terjadi kesalahan jaringan/API untuk '{food_name}': {e}")
            return None


# =====================================================================
# 2. KELAS PEMROSES DATA MET (METABOLIC EQUIVALENT OF TASK)
# =====================================================================

class MetDataProcessor:
    """
    Kelas untuk mengelola pemrosesan, pembersihan, dan pemfilteran berkas CSV MET.
    """
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _create_default_csv(self, file_path: str):
        """
        Membuat berkas CSV MET default jika berkas tersebut belum ada di direktori lokal.
        """
        default_data = """activity_code,activity_category,activity_name,met_value
101,Conditioning,Push-ups (vigorous effort),8.0
102,Conditioning,Push-ups (moderate effort),3.8
103,Conditioning,Sit-ups (moderate effort),3.8
104,Conditioning,Sit-ups (vigorous effort),8.0
105,Conditioning,Squats,5.0
106,Conditioning,Plank,3.5
107,Running,Running 5 mph (12 min/mile),8.3
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(default_data)
        print(f"[INFO] Berkas input '{file_path}' berhasil dibuat secara otomatis.")

    def process_met_data(self, file_path: str = "met_activities.csv", target_exercises: List[str] = None) -> pd.DataFrame:
        """
        Membaca berkas CSV MET, melakukan pembersihan data, dan memfilter latihan target.
        """
        print(f"\n[INFO] Memproses data MET dari berkas: '{file_path}'...")
        
        # Buat berkas default jika tidak ditemukan
        if not os.path.exists(file_path):
            self._create_default_csv(file_path)
            
        if target_exercises is None:
            target_exercises = ['Push-ups (moderate effort)', 'Sit-ups (moderate effort)', 'Squats', 'Plank']
            
        try:
            # Membaca CSV menggunakan Pandas
            df = pd.read_csv(file_path)
            
            # Pembersihan data (strip whitespace pada header kolom dan teks)
            df.columns = df.columns.str.strip()
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].astype(str).str.strip()
                
            # Filter hanya latihan yang dibutuhkan aplikasi
            filtered_df = df[df['activity_name'].isin(target_exercises)].copy()
            
            print(f"  [SUCCESS] Berhasil memproses {len(filtered_df)} gerakan MET target.")
            print(filtered_df.to_string(index=False))
            
            return filtered_df
        except Exception as e:
            print(f"  [ERROR] Gagal memproses berkas MET: {e}")
            return pd.DataFrame()


# =====================================================================
# 3. ALUR UTAMA PROGRAM (MAIN EXECUTION)
# =====================================================================

def main():
    print("========================================================")
    print("       SmartCoach Data Scraping & MET Integration")
    print("========================================================\n")
    
    output_dir = "output"
    
    # Inisialisasi Kelas
    nutrition_scraper = FoodNutritionScraper(output_dir)
    met_processor = MetDataProcessor(output_dir)
    
    # --- BAGIAN 1: SCRAPING NUTRISI MAKANAN ---
    file_makanan = "makanan.txt"
    if os.path.exists(file_makanan):
        with open(file_makanan, "r", encoding="utf-8") as f:
            daftar_makanan = [line.strip() for line in f if line.strip()]
    else:
        # Default list makanan jika makanan.txt belum tersedia
        daftar_makanan = ["Chicken Breast", "Nasi Putih", "Tempe Goreng", "Greek Yogurt"]
        with open(file_makanan, "w", encoding="utf-8") as f:
            f.write("\n".join(daftar_makanan))
        print(f"[INFO] Berkas '{file_makanan}' tidak ditemukan. Membuat berkas contoh.")

    print(f"[INFO] Memulai scraping nutrisi untuk {len(daftar_makanan)} makanan...")
    nutrition_results = []
    
    for food in daftar_makanan:
        info = nutrition_scraper.get_nutrition_data(food)
        if info:
            nutrition_results.append(info)
        time.sleep(1.0)  # Jeda 1 detik agar tidak diblokir API
        
    # Menyimpan output nutrisi secara lokal (JSON dan CSV)
    if nutrition_results:
        # Simpan JSON
        json_path = os.path.join(output_dir, "nutrisi_makanan.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(nutrition_results, f, ensure_ascii=False, indent=4)
        print(f"\n[SUCCESS] Data Nutrisi disimpan ke JSON: {json_path}")
        
        # Simpan CSV
        df_nutrition = pd.DataFrame(nutrition_results)
        csv_path = os.path.join(output_dir, "nutrisi_makanan.csv")
        df_nutrition.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"[SUCCESS] Data Nutrisi disimpan ke CSV: {csv_path}")
    else:
        print("\n[WARN] Tidak ada data nutrisi yang berhasil diambil.")

    # --- BAGIAN 2: PROSES DATA MET ---
    target_exercises = ['Push-ups (moderate effort)', 'Sit-ups (moderate effort)', 'Squats', 'Plank']
    df_met = met_processor.process_met_data("met_activities.csv", target_exercises)
    
    if not df_met.empty:
        # Menyimpan output MET secara lokal (CSV dan JSON)
        met_csv_path = os.path.join(output_dir, "processed_met.csv")
        df_met.to_csv(met_csv_path, index=False, encoding="utf-8")
        print(f"[SUCCESS] Data MET disimpan ke CSV: {met_csv_path}")
        
        met_json_path = os.path.join(output_dir, "processed_met.json")
        df_met.to_json(met_json_path, orient="records", indent=4, force_ascii=False)
        print(f"[SUCCESS] Data MET disimpan ke JSON: {met_json_path}")
    else:
        print("\n[WARN] Data MET kosong atau gagal diproses.")

    print("\n========================================================")
    print("      PROSES SELESAI: SEMUA OUTPUT DISIMPAN DI LOKAL")
    print("========================================================")

if __name__ == "__main__":
    main()