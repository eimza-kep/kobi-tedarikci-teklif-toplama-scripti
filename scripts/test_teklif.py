# -*- coding: utf-8 -*-
"""
test_teklif.py
--------------
Tedarikçi Teklif Toplama, Karşılaştırma Matrisi ve
KEP Satın Alma Sözleşmesi birim ve entegrasyon testleri.
"""

import unittest
import os
import sys
import sqlite3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from scripts.rfq_comparison_engine import (
    analyze_rfq_group,
    score_payment_terms,
    score_shipping_terms,
    generate_acceptance_email
)
from scripts.kep_purchase_contract import (
    validate_kep_address,
    generate_purchase_order_contract,
    generate_contract_html,
    generate_kep_transmission_package
)

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
        self.assertIsNotNone(cur.fetchone(), "rfq_quotes tablosu oluşturulmuş olmalıdır.")
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        self.assertIsNotNone(cur.fetchone(), "settings tablosu oluşturulmuş olmalıdır.")

    def test_quote_insert_and_retrieve(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO rfq_quotes (
                tracking_code, supplier_name, supplier_vkn, contact_person,
                supplier_phone, supplier_email, supplier_city, supplier_kep,
                rfq_category, rfq_ref, total_amount, currency, payment_terms,
                delivery_days, validity_date, shipping_terms, quote_details,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "TEKLIF-TEST-001",
            "Atlas Ambalaj Sanayi A.Ş.",
            "1234567890",
            "Burak Kaya",
            "02125554433",
            "teklif@atlas.com",
            "İstanbul",
            "atlasambalaj@hs01.kep.tr",
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
        self.assertEqual(record["supplier_kep"], "atlasambalaj@hs01.kep.tr")

    def test_quote_status_update(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO rfq_quotes (tracking_code, supplier_name, status)
            VALUES (?, ?, ?)
        """, ("TEKLIF-TEST-002", "Nova IT Ltd.", "Teklif Alındı"))
        self.conn.commit()

        cur.execute("""
            UPDATE rfq_quotes
            SET status = 'Kabul Edildi (KEP ile Tebliğ Edildi)'
            WHERE tracking_code = 'TEKLIF-TEST-002'
        """)
        self.conn.commit()

        cur.execute("SELECT status FROM rfq_quotes WHERE tracking_code = 'TEKLIF-TEST-002'")
        row = cur.fetchone()
        self.assertEqual(row["status"], "Kabul Edildi (KEP ile Tebliğ Edildi)")

    def test_kep_address_validator(self):
        # Geçerli KEP adresleri
        self.assertTrue(validate_kep_address("sirket@hs01.kep.tr")["valid"])
        self.assertTrue(validate_kep_address("atlas@ptt.hs01.kep.tr")["valid"])
        self.assertTrue(validate_kep_address("avukat@tnb.hs01.kep.tr")["valid"])

        # Geçersiz adresler
        self.assertFalse(validate_kep_address("normal@gmail.com")["valid"])
        self.assertFalse(validate_kep_address("firma@kep.com")["valid"])
        self.assertFalse(validate_kep_address("")["valid"])
        self.assertFalse(validate_kep_address(None)["valid"])

    def test_rfq_comparison_matrix(self):
        sample_quotes = [
            {
                "tracking_code": "TEKLIF-TEST-A",
                "supplier_name": "Tedarikçi A (Pahalı ama 90 gün vade)",
                "total_amount": 100000.0,
                "delivery_days": 15,
                "payment_terms": "90 Gün Vadeli",
                "shipping_terms": "DDP"
            },
            {
                "tracking_code": "TEKLIF-TEST-B",
                "supplier_name": "Tedarikçi B (En Ucuz & Hızlı)",
                "total_amount": 75000.0,
                "delivery_days": 3,
                "payment_terms": "30 Gün Vadeli",
                "shipping_terms": "DDP"
            },
            {
                "tracking_code": "TEKLIF-TEST-C",
                "supplier_name": "Tedarikçi C (Peşin ve Geç)",
                "total_amount": 95000.0,
                "delivery_days": 20,
                "payment_terms": "Peşin",
                "shipping_terms": "Ex-Works"
            }
        ]

        matrix = analyze_rfq_group(sample_quotes)
        self.assertEqual(len(matrix), 3)

        # Tedarikçi B en ucuz ve en hızlı olmalı
        b_quote = next(q for q in matrix if q["tracking_code"] == "TEKLIF-TEST-B")
        self.assertTrue(b_quote["is_lowest_price"])
        self.assertTrue(b_quote["is_fastest_delivery"])
        self.assertTrue(b_quote["is_best_value"], "Tedarikçi B en avantajlı teklif seçilmelidir.")

        # Tedarikçi C en düşük puana sahip olmalı
        c_quote = next(q for q in matrix if q["tracking_code"] == "TEKLIF-TEST-C")
        self.assertFalse(c_quote["is_best_value"])
        self.assertLess(c_quote["score"], b_quote["score"])

    def test_acceptance_email_generator(self):
        sample = {
            "tracking_code": "TEKLIF-TEST-EML",
            "supplier_name": "Mega Tedarik A.Ş.",
            "supplier_email": "satis@megatedarik.com",
            "total_amount": 250000.0,
            "currency": "TRY (₺)",
            "payment_terms": "60 Gün Vadeli",
            "delivery_days": 5,
            "rfq_ref": "RFQ-2026-HAMMADDE"
        }
        res = generate_acceptance_email(sample)
        self.assertIn("TEKLIF-TEST-EML", res["subject"])
        self.assertIn("250,000.00 TRY (₺)", res["body"])
        self.assertIn("Mega Tedarik A.Ş.", res["body"])
        self.assertEqual(res["supplier_email"], "satis@megatedarik.com")

    def test_purchase_order_contract_and_html(self):
        sample = {
            "id": 88,
            "tracking_code": "TEKLIF-TEST-CTR",
            "supplier_name": "Doğu Çimento Sanayi",
            "supplier_vkn": "9988776655",
            "supplier_kep": "dogucimento@hs01.kep.tr",
            "total_amount": 500000.0,
            "currency": "TRY (₺)",
            "payment_terms": "60 Gün Vadeli",
            "delivery_days": 14,
            "shipping_terms": "DDP Şantiye Teslim",
            "quote_details": "1000 ton Portland Çimento temini"
        }

        contract = generate_purchase_order_contract(sample)
        self.assertIn("SOZLESME-2026-00088", contract["contract_no"])
        self.assertIn("dogucimento@hs01.kep.tr", contract["supplier_kep"])
        self.assertEqual(contract["amount"], 500000.0)
        self.assertEqual(contract["vat_amount"], 100000.0)
        self.assertEqual(contract["total_with_vat"], 600000.0)
        self.assertIn("TTK m. 18/3", contract["contract_text"])

        html = generate_contract_html(sample)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("SOZLESME-2026-00088", html)
        self.assertIn("Doğu Çimento Sanayi", html)
        self.assertIn("600,000.00 TRY (₺)", html)

    def test_kep_transmission_package(self):
        sample = {
            "id": 12,
            "tracking_code": "TEKLIF-TEST-KEP",
            "supplier_name": "Test Lojistik A.Ş.",
            "supplier_vkn": "5554443322",
            "supplier_kep": "testlojistik@hs01.kep.tr",
            "total_amount": 80000.0
        }
        pkg = generate_kep_transmission_package(sample)
        self.assertEqual(pkg["status"], "success")
        self.assertTrue(pkg["message_id"].startswith("KEP-2026-MSG-"))
        self.assertTrue(pkg["mazbata_code"].startswith("DELIL-2026-TR-"))
        self.assertEqual(len(pkg["sha256_hash"]), 64, "SHA-256 hash uzunluğu 64 karakter olmalıdır.")
        self.assertEqual(pkg["recipient_kep"], "testlojistik@hs01.kep.tr")

    def test_buyer_settings(self):
        data = {
            "title": "Anadolu Holding Satın Alma A.Ş.",
            "vkn": "7778889999",
            "kep_address": "anadoluholding@hs01.kep.tr"
        }
        server.save_buyer_settings(data)
        settings = server.get_buyer_settings()
        self.assertEqual(settings["title"], "Anadolu Holding Satın Alma A.Ş.")
        self.assertEqual(settings["vkn"], "7778889999")
        self.assertEqual(settings["kep_address"], "anadoluholding@hs01.kep.tr")

    def test_files_exist(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "index.html")), "index.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "admin.html")), "admin.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "api.php")), "api.php bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "scripts", "rfq_comparison_engine.py")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "scripts", "kep_purchase_contract.py")))

if __name__ == "__main__":
    print("=" * 60)
    print("  KOBİ TEDARİKÇİ TEKLİF & KEP SÖZLEŞME TEST SÜİTİ")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRFQSystem)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("\n✅ TÜM BİRİM VE ENTEGRASYON TESTLERİ BAŞARIYLA GEÇTİ!")
        sys.exit(0)
    else:
        print("\n❌ TEST BAŞARISIZ!")
        sys.exit(1)
