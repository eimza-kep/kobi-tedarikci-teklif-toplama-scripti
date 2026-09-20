import http.server
import socketserver
import json
import sqlite3
import os
import sys
import random
from urllib.parse import urlparse

PORT = 8090
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tedarikci_teklifler.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rfq_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_code TEXT UNIQUE,
            supplier_name TEXT,
            supplier_vkn TEXT,
            contact_person TEXT,
            supplier_phone TEXT,
            supplier_email TEXT,
            supplier_city TEXT,
            rfq_category TEXT,
            rfq_ref TEXT,
            total_amount REAL,
            currency TEXT,
            payment_terms TEXT,
            delivery_days INTEGER,
            validity_date TEXT,
            shipping_terms TEXT,
            quote_details TEXT,
            status TEXT DEFAULT 'Teklif Alındı',
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

class RFQHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_file("index.html", "text/html; charset=utf-8")
        elif path in ("/admin", "/admin.html"):
            self.send_file("admin.html", "text/html; charset=utf-8")
        elif path == "/health":
            self.send_json({"status": "ok", "app": "kobi-tedarikci-teklif-toplama-scripti", "port": PORT})
        elif path == "/api/teklifler":
            self.handle_get_quotes()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/teklif-ver":
            self.handle_create_quote()
        elif path == "/api/durum-guncelle":
            self.handle_update_status()
        else:
            self.send_error(404, "Endpoint not found")

    def send_file(self, filename, content_type):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if not os.path.exists(filepath):
            self.send_error(404, f"File {filename} not found")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def handle_create_quote(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code") or f"TEKLIF-2026-{random.randint(1000, 9999)}"

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO rfq_quotes (
                    tracking_code, supplier_name, supplier_vkn, contact_person,
                    supplier_phone, supplier_email, supplier_city, rfq_category,
                    rfq_ref, total_amount, currency, payment_terms,
                    delivery_days, validity_date, shipping_terms, quote_details,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tracking_code,
                data.get("supplier_name", ""),
                data.get("supplier_vkn", ""),
                data.get("contact_person", ""),
                data.get("supplier_phone", ""),
                data.get("supplier_email", ""),
                data.get("supplier_city", ""),
                data.get("rfq_category", ""),
                data.get("rfq_ref", ""),
                float(data.get("total_amount", 0)),
                data.get("currency", "TRY"),
                data.get("payment_terms", ""),
                int(data.get("delivery_days", 1)),
                data.get("validity_date", ""),
                data.get("shipping_terms", ""),
                data.get("quote_details", ""),
                data.get("status", "Teklif Alındı"),
                data.get("created_at", "")
            ))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "tracking_code": tracking_code})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_get_quotes(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM rfq_quotes ORDER BY id DESC")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            self.send_json(rows)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_update_status(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code")
            new_status = data.get("status")

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("UPDATE rfq_quotes SET status = ? WHERE tracking_code = ?", (new_status, tracking_code))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "updated": tracking_code})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", PORT))
    print(f"🚀 Tedarikci Teklif Portali Baslatildi: http://localhost:{port}")
    print(f"📊 Satin Alma Yonetim Paneli: http://localhost:{port}/admin")
    with socketserver.TCPServer(("", port), RFQHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu kapatildi.")
