import time
import requests
import pymysql
from datetime import datetime
from dotenv import load_dotenv
import os

# 1. 환경변수 로드
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

UPBIT_BASE_URL = os.getenv("UPBIT_BASE_URL")

# 2. DB 연결 함수
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

# 3. 업비트 현재가 조회
def fetch_current_prices():
    url = f"{UPBIT_BASE_URL}v1/ticker"
    params = {
        "markets": "KRW-BTC,KRW-ETH"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

# 4. DB에 시세 저장
def save_prices_to_db(prices):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        sql = """
        INSERT INTO coin_history (coin_code, price, collected_at)
        VALUES (%s, %s, %s)
        """
        for item in prices:
            coin_code = item["market"]      # KRW-BTC
            price = item["trade_price"]     # 현재가
            collected_at = datetime.now()   # 수집 시각
            cur.execute(sql, (coin_code, price, collected_at))
        cur.close()
    finally:
        conn.close()

# 5. 주기적 실행 (1분)
def run_collector():
    print("데이터 수집을 시작합니다...")
    while True:
        try:
            prices = fetch_current_prices()
            save_prices_to_db(prices)
            print(f"[{datetime.now()}] 데이터 저장 완료")
        except Exception as e:
            print(f"오류 발생: {e}")
        
        # 60초 대기
        time.sleep(60)

if __name__ == "__main__":
    run_collector()