VADE_ISKONTO_CARPANI = {'pesin_indirim': 0.05, '30_gun': 0.0, '60_gun': 0.04}
# -*- coding: utf-8 -*-
"""
server.py
---------
KOBİ Tedarikçi Teklif Toplama, Karşılaştırma Matrisi, GİB UBL-TR 2.1 Order XML
ve KEP Satın Alma Sözleşmesi Sunucusu.
"""

import http.server
import socketserver
import json
import sqlite3
import os
import sys
import random
from urllib.parse import urlparse, parse_qs

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.rfq_comparison_engine import (
    analyze_rfq_group,
    generate_acceptance_email,
    generate_comparison_matrix_html,
    generate_comparison_matrix_csv
)
from scripts.rfq_order_xml_generator import generate_ubl_order_xml
from scripts.kep_purchase_contract import (
    validate_kep_address,
    generate_contract_html,
    generate_kep_transmission_package,
    DEFAULT_BUYER
)

PORT = int(os.environ.get("PORT", 8090))
DB_FILE = os.environ.get("DATABASE_PATH", os.path.join(ROOT_DIR, "tedarikci_teklifler.db"))

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
            supplier_kep TEXT DEFAULT '',
            rfq_category TEXT,
            rfq_ref TEXT,
            total_amount REAL,
            discount_amount REAL DEFAULT 0.0,
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
    # Kolon göçlerini (migrations) kontrol et
    cur.execute("PRAGMA table_info(rfq_quotes)")
    cols = [col[1] for col in cur.fetchall()]
    if "supplier_kep" not in cols:
        cur.execute("ALTER TABLE rfq_quotes ADD COLUMN supplier_kep TEXT DEFAULT ''")
    if "discount_amount" not in cols:
        cur.execute("ALTER TABLE rfq_quotes ADD COLUMN discount_amount REAL DEFAULT 0.0")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_buyer_settings():
    settings = dict(DEFAULT_BUYER)
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM settings")
        for key, value in cur.fetchall():
            if value:
                settings[key] = value
    return settings

def save_buyer_settings(data):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        for key, val in data.items():
            cur.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(key), str(val))
            )
        conn.commit()

class RFQHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self.send_file("index.html", "text/html; charset=utf-8")
        elif path in ("/admin", "/admin.html"):
            self.send_file("admin.html", "text/html; charset=utf-8")
        elif path == "/health":
            self.send_json({"status": "ok", "app": "kobi-tedarikci-teklif-toplama-scripti", "port": PORT})
        elif path == "/api/teklifler":
            self.handle_get_quotes()
        elif path == "/api/ayarlar":
            self.send_json(get_buyer_settings())
        elif path == "/api/karsilastirma-matrisi":
            self.handle_comparison_matrix(qs)
        elif path == "/api/karsilastirma-raporu-html":
            self.handle_comparison_report_html(qs)
        elif path == "/api/karsilastirma-raporu-csv":
            self.handle_comparison_report_csv(qs)
        elif path == "/api/export-order-xml":
            self.handle_export_order_xml(qs)
        elif path == "/api/satin-alma-sozlesmesi":
            self.handle_purchase_contract(qs)
        elif path == "/api/kabul-eposta":
            self.handle_acceptance_email(qs)
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/teklif-ver":
            self.handle_create_quote()
        elif path == "/api/durum-guncelle":
            self.handle_update_status()
        elif path == "/api/ayarlar":
            self.handle_save_settings()
        elif path == "/api/kep-gonder":
            self.handle_kep_transmission()
        elif path == "/api/kep-dogrula":
            self.handle_kep_validate()
        else:
            self.send_error(404, "Endpoint not found")

    def send_file(self, filename, content_type):
        filepath = os.path.join(ROOT_DIR, filename)
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
        self.end_headers()
        self.wfile.write(body)

    def get_quote_by_code(self, tracking_code):
        if not tracking_code:
            return None
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM rfq_quotes WHERE tracking_code = ?", (tracking_code,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

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
                    supplier_phone, supplier_email, supplier_city, supplier_kep,
                    rfq_category, rfq_ref, total_amount, discount_amount, currency, payment_terms,
                    delivery_days, validity_date, shipping_terms, quote_details,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tracking_code,
                data.get("supplier_name", ""),
                data.get("supplier_vkn", ""),
                data.get("contact_person", ""),
                data.get("supplier_phone", ""),
                data.get("supplier_email", ""),
                data.get("supplier_city", ""),
                data.get("supplier_kep", ""),
                data.get("rfq_category", ""),
                data.get("rfq_ref", ""),
                float(data.get("total_amount", 0)),
                float(data.get("discount_amount", 0)),
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

    def handle_comparison_matrix(self, qs):
        ref_filter = qs.get("rfq_ref", [""])[0]
        cat_filter = qs.get("category", [""])[0]

        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if ref_filter:
                cur.execute("SELECT * FROM rfq_quotes WHERE rfq_ref = ?", (ref_filter,))
            elif cat_filter:
                cur.execute("SELECT * FROM rfq_quotes WHERE rfq_category = ?", (cat_filter,))
            else:
                cur.execute("SELECT * FROM rfq_quotes")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

            analysis = analyze_rfq_group(rows)
            self.send_json({"status": "success", "matrix": analysis, "count": len(analysis)})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_comparison_report_html(self, qs):
        ref_filter = qs.get("rfq_ref", [""])[0]
        cat_filter = qs.get("category", [""])[0]

        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if ref_filter:
                cur.execute("SELECT * FROM rfq_quotes WHERE rfq_ref = ?", (ref_filter,))
            elif cat_filter:
                cur.execute("SELECT * FROM rfq_quotes WHERE rfq_category = ?", (cat_filter,))
            else:
                cur.execute("SELECT * FROM rfq_quotes")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

            buyer = get_buyer_settings()
            report_title = ref_filter or cat_filter or "Tüm Teklifler"
            html = generate_comparison_matrix_html(report_title, rows, buyer)
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_error(500, str(e))

    def handle_comparison_report_csv(self, qs):
        ref_filter = qs.get("rfq_ref", [""])[0]
        cat_filter = qs.get("category", [""])[0]

        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if ref_filter:
                cur.execute("SELECT * FROM rfq_quotes WHERE rfq_ref = ?", (ref_filter,))
            elif cat_filter:
                cur.execute("SELECT * FROM rfq_quotes WHERE rfq_category = ?", (cat_filter,))
            else:
                cur.execute("SELECT * FROM rfq_quotes")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

            report_title = ref_filter or cat_filter or "genel"
            csv_text = generate_comparison_matrix_csv(report_title, rows)
            body = csv_text.encode("utf-8")
            safe_filename = f"teklif_karsilastirma_{report_title.replace(' ', '_')}.csv"
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{safe_filename}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_error(500, str(e))

    def handle_export_order_xml(self, qs):
        tracking_code = qs.get("tracking_code", [""])[0]
        quote = self.get_quote_by_code(tracking_code)
        if not quote:
            self.send_error(404, f"'{tracking_code}' takip kodlu teklif bulunamadı.")
            return

        buyer = get_buyer_settings()
        xml_content = generate_ubl_order_xml(quote, buyer)
        body = xml_content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="siparis_{tracking_code}.xml"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_purchase_contract(self, qs):
        tracking_code = qs.get("tracking_code", [""])[0]
        quote = self.get_quote_by_code(tracking_code)
        if not quote:
            self.send_error(404, f"'{tracking_code}' takip kodlu teklif bulunamadı.")
            return

        buyer = get_buyer_settings()
        html = generate_contract_html(quote, buyer)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_acceptance_email(self, qs):
        tracking_code = qs.get("tracking_code", [""])[0]
        quote = self.get_quote_by_code(tracking_code)
        if not quote:
            self.send_error(404, f"'{tracking_code}' takip kodlu teklif bulunamadı.")
            return

        buyer = get_buyer_settings()
        email_data = generate_acceptance_email(quote, buyer)
        self.send_json(email_data)

    def handle_kep_validate(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            kep_addr = data.get("kep_address", "")
            res = validate_kep_address(kep_addr)
            self.send_json(res)
        except Exception as e:
            self.send_json({"valid": False, "reason": str(e)}, status=400)

    def handle_kep_transmission(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code")
            supplier_kep = data.get("supplier_kep", "").strip()

            quote = self.get_quote_by_code(tracking_code)
            if not quote:
                self.send_json({"status": "error", "message": "Teklif bulunamadı."}, status=404)
                return

            if supplier_kep:
                quote["supplier_kep"] = supplier_kep

            buyer = get_buyer_settings()
            pkg = generate_kep_transmission_package(quote, buyer)

            # Durumu KEP ile Onaylandı yap
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("""
                UPDATE rfq_quotes
                SET status = 'Kabul Edildi (KEP ile Tebliğ Edildi)', supplier_kep = ?
                WHERE tracking_code = ?
            """, (quote.get("supplier_kep", ""), tracking_code))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "package": pkg})
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

    def handle_save_settings(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            save_buyer_settings(data)
            self.send_json({"status": "success", "message": "Alıcı ayarları kaydedildi."})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=400)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", PORT))
    print(f"🚀 Tedarikçi Teklif Portalı Başlatıldı: http://localhost:{port}")
    print(f"📊 Satın Alma Yönetim Paneli: http://localhost:{port}/admin")
    with socketserver.TCPServer(("", port), RFQHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu kapatıldı.")
