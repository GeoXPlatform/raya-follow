import requests
from bs4 import BeautifulSoup
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json

# قراءة المفتاح السري المخفي في جيت هاب
firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
if not firebase_creds_json:
    print("Error: FIREBASE_CREDENTIALS environment variable not set.")
    exit(1)

# تسجيل الدخول لفايربيس
cred_dict = json.loads(firebase_creds_json)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://geox-platform-default-rtdb.firebaseio.com'
})

codes = set()
try:
    # جلب الأكواد من المخزن الأساسي والفرعي
    ref_main = db.reference('rayaCRM/stock/main')
    ref_branch = db.reference('rayaCRM/stock/branch')
    
    for ref in [ref_main, ref_branch]:
        data = ref.get()
        if data:
            for item in data:
                if '_code' in item and item['_code'] != '-':
                    codes.add(item['_code'])
                    
    print(f"Found {len(codes)} unique codes in Firebase.")
except Exception as e:
    print(f"Error fetching codes from Firebase: {e}")

scraped_data = {}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

print(f"Starting to scrape from RayaShop...")
for code in codes:
    try:
        # البحث برقم الكود في راية شوب مع تصفية البائع (راية)
        search_url = f"https://www.rayashop.com/ar/catalogsearch/result/?q={code}&seller=raya"
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # استخراج السعر
        price_element = soup.find(class_='price')
        
        # استخراج اللينك المباشر للمنتج
        product_link = "#"
        link_element = soup.find('a', class_='product-item-link')
        if link_element and 'href' in link_element.attrs:
            product_link = link_element['href']

        if price_element:
            scraped_data[code] = {
                'price': price_element.text.strip(),
                'url': product_link
            }
            print(f"✅ Found Raya info for {code}")
        else:
             print(f"❌ Not found: {code}")
    except Exception as e:
        print(f"⚠️ Error with {code}: {e}")

# حفظ السعر واللينك في فايربيس
try:
    prices_ref = db.reference('rayaCRM/livePrices')
    prices_ref.set(scraped_data)
    print("Prices and URLs successfully updated to Firebase!")
except Exception as e:
    print(f"Error saving to Firebase: {e}")
