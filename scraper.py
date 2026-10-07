import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import glob

excel_files = glob.glob("*.xlsx") + glob.glob("*.xlsm")
codes = set()

for file in excel_files:
    try:
        df = pd.read_excel(file)
        code_col = None
        for col in df.columns:
            col_name = str(col).lower()
            if "كود" in col_name or "code" in col_name or "صنف" in col_name or "item" in col_name:
                code_col = col
                break
        
        if code_col:
            file_codes = df[code_col].dropna().astype(str).tolist()
            for c in file_codes:
                clean_code = c.strip()
                if clean_code and clean_code.lower() not in ["-", "nan", "none"]:
                    codes.add(clean_code)
    except Exception as e:
        print(f"Error reading {file}: {e}")

prices_data = {}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

for code in codes:
    try:
        url = f"https://www.rayashop.com/ar/catalogsearch/result/?q={code}"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        price_element = soup.find(class_='price')
        if price_element:
            prices_data[code] = price_element.text.strip()
    except Exception as e:
        print(f"Error with {code}: {e}")

with open('prices.json', 'w', encoding='utf-8') as f:
    json.dump(prices_data, f, ensure_ascii=False, indent=4)
