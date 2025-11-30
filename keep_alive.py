# keep_alive.py (Ví dụ dùng cổng 8080)
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bố Mày Sống Rồi Đấy"

def run():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
