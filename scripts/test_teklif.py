import unittest
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

class TestRFQSystem(unittest.TestCase):
    def setUp(self):
        server.init_db()
        self.conn = sqlite3.connect(server.DB_FILE)
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        cur.execute("DELETE FROM rfq_quotes WHERE tracking_code LIKE 'TEKLIF-TEST%'")
        self.conn.commit()

    def tearDown(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM rfq_quotes WHERE tracking_code LIKE 'TEKLIF-TEST%'")
        self.conn.commit()
        self.conn.close()

    def test_database_table_exists(self):
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rfq_quotes'")
        row = cur.fetchone()
        self.assertIsNotNone(row, "rfq_quotes tablosu oluşturulmuş olmalıdır.")

    def test_quote_insert_and_retrieve(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO rfq_quotes (
                tracking_code, supplier_name, supplier_vkn, contact_person,
                supplier_phone, supplier_email, supplier_city, rfq_category,
                rfq_ref, total_amount, currency, payment_terms,
                delivery_days, validity_date, shipping_terms, quote_details,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "TEKLIF-TEST-001",
            "Atlas Ambalaj Sanayi A.Ş.",
            "1234567890",
            "Burak Kaya",
            "02125554433",
            "teklif@atlas.com",
            "İstanbul",
            "Hammadde & Yarı Mamul",
            "RFQ-2026-05",
            175000.0,
            "TRY (₺)",
            "60 Gün Vadeli",
            10,
            "2026-10-15",
            "Satıcı Tarafından Adrese Teslim (DDP)",
            "100.000 adet oluklu mukavva koli",
            "Teklif Alındı",
            "2026-09-20T10:00:00Z"
        ))
        self.conn.commit()

        cur.execute("SELECT * FROM rfq_quotes WHERE tracking_code = 'TEKLIF-TEST-001'")
        record = cur.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record["supplier_name"], "Atlas Ambalaj Sanayi A.Ş.")
        self.assertEqual(record["total_amount"], 175000.0)

    def test_quote_status_update(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO rfq_quotes (tracking_code, supplier_name, status)
            VALUES (?, ?, ?)
        """, ("TEKLIF-TEST-002", "Nova IT Ltd.", "Teklif Alındı"))
        self.conn.commit()

        cur.execute("""
            UPDATE rfq_quotes
            SET status = 'Kabul Edildi (Sipariş Verildi)'
            WHERE tracking_code = 'TEKLIF-TEST-002'
        """)
        self.conn.commit()

        cur.execute("SELECT status FROM rfq_quotes WHERE tracking_code = 'TEKLIF-TEST-002'")
        row = cur.fetchone()
        self.assertEqual(row["status"], "Kabul Edildi (Sipariş Verildi)")

    def test_files_exist(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "index.html")), "index.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "admin.html")), "admin.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "api.php")), "api.php bulunamadı")

if __name__ == "__main__":
    unittest.main()
