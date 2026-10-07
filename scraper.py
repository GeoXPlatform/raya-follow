import requests
from bs4 import BeautifulSoup
import json
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

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
    # جلب الأكواد من المخزن اللي إنت رفعته على الموقع
    ref_main = db.reference('rayaCRM/stock/main')
    ref_branch = db.reference('rayaCRM/stock/branch')
    
    main_data = ref_main.get()
    if main_data:
        for item in main_data:
            if '_code' in item and item['_code'] != '-':
                codes.add(item['_code'])

    branch_data = ref_branch.get()
    if branch_data:
        for item in branch_data:
            if '_code' in item and item['_code'] != '-':
                codes.add(item['_code'])
                
    print(f"Found {len(codes)} unique codes in Firebase.")
except Exception as e:
    print(f"Error fetching codes from Firebase: {e}")

prices_data = {}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

print(f"Starting to scrape prices from RayaShop...")
for code in codes:
    try:
        # البحث في راية شوب وتصفية بائع "راية" فقط
        url = f"https://www.rayashop.com/ar/catalogsearch/result/?q={code}&seller=raya"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        price_element = soup.find(class_='price')
        if price_element:
            prices_data[code] = price_element.text.strip()
            print(f"✅ Found Raya price for {code}")
        else:
             print(f"❌ Not found: {code}")
    except Exception as e:
        print(f"⚠️ Error with {code}: {e}")

# حفظ الأسعار الجديدة في فايربيس عشان الموقع يقراها فوراً
try:
    prices_ref = db.reference('rayaCRM/livePrices')
    prices_ref.set(prices_data)
    print("Prices successfully updated to Firebase!")
except Exception as e:
    print(f"Error saving to Firebase: {e}")
