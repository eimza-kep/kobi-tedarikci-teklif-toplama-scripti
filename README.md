# 📊 KOBİ Tedarikçi Teklif Toplama, Karşılaştırma Matrisi, UBL-TR 2.1 & KEP Satın Alma Portalı

[![CI Test Suite](https://github.com/eimza-kep/kobi-tedarikci-teklif-toplama-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kobi-tedarikci-teklif-toplama-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kobi-tedarikci-teklif-toplama-scripti/)
[![UBL-TR 2.1 Destekli](https://img.shields.io/badge/UBL--TR%202.1-Order%20XML-purple.svg)](#)
[![KEP Destekli](https://img.shields.io/badge/KEP%20S%C3%B6zle%C5%9Fme-TTK%2018%2F3-blue.svg)](#)
[![Karşılaştırma](https://img.shields.io/badge/RFQ%20Analiz-Matris%20Puanlama-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)

KOBİ'ler, şirketler, fabrikalar ve satın alma departmanları için; tedarikçilerden gelen fiyat tekliflerini (RFQ - Request for Quotation) tek bir havuzda toplayan, **en uygun fiyat, iskonto ve vade karşılaştırma matrisi sunan**, **GİB UBL-TR 2.1 Satın Alma Sipariş Fişi (Order XML) üreten**, **Türk Ticaret Kanunu (TTK m. 18/3) uyumlu Resmi Satın Alma Sözleşmesi çıkaran** ve **KEP (Kayıtlı Elektronik Posta) üzerinden resmi sipariş tebliği yapan** açık kaynaklı kurumsal satın alma yazılımı.

---

## 🎯 Temel Yetenekler & Özellikler

1. **Tedarikçi Karşılaştırma Matrisi ve Çok Kriterli Puanlama:**
   - Aynı satınalma talebine veya kategoriye ait teklifleri tek ekranda yan yana karşılaştırır.
   - Çok kriterli ağırlıklı puanlama motoru: **Net Fiyat (%45)**, **Ödeme Vadesi (%25)**, **Teslimat Süresi (%20)**, **Nakliye Şartları (%10)** ve **İskonto Teşvik Bonusu (+5 Puan)**.
   - En iyi teklife **🏆 En Avantajlı Teklif**, en ucuz teklife **🏷️ En Düşük Fiyat**, en süratli teklife **⚡ En Hızlı Teslimat** ve indirim sunan teklife **🏷️ İskontolu** rozetleri atar.
   - Tek tıkla tedarikçiye gönderilmek üzere hazırlanmış **Resmi Kabul E-Postası Şablonu**.

2. **GİB UBL-TR 2.1 Satın Alma Sipariş Fişi (Order XML) Üretimi:**
   - Onaylanan veya siparişe dönüştürülen teklifler için Gelir İdaresi Başkanlığı (GİB) UBL-TR 2.1 standardında geçerli `Order` XML belgesi üretir.
   - ERP ve muhasebe programlarına (Logo, Mikro, Netsis, Zirve vb.) veya özel entegratör e-Sipariş sistemlerine doğrudan aktarılabilir.
   - CustomizationID: `TR1.2`, ProfileID: `TICARISIPARIS`, Party Identification (VKN/TCKN), KDV dökümü, İskonto (`cac:AllowanceCharge`) ve parasal toplamlar (`cac:AnticipatedMonetaryTotal`).

3. **Yazdırılabilir A4 Karşılaştırma Raporu & Komisyon Karar Tutanağı:**
   - Şirket yönetim kuruluna veya genel müdür onayına sunulmak üzere tek tıkla A4 formatında **Satın Alma Teklif Karşılaştırma ve Komisyon Karar Raporu (HTML / PDF)** üretir.
   - İhale özet istatistikleri (ortalama teklif, en düşük teklif, en hızlı teslim), karşılaştırmalı teklif tablosu ve yetkili imza blokları içerir.
   - Excel doğrudan açılımı için **UTF-8 with BOM destekli CSV karşılaştırma raporu** ihracı.

4. **KEP Üzerinden Resmi Satın Alma Sözleşmesi (TTK m. 18/3):**
   - Teklif kabul edildiğinde resmi A4 formatında yazdırılabilir / PDF kaydedilebilir **Satın Alma Sözleşmesi** üretir.
   - Tedarikçi KEP adresi (`firma@hs01.kep.tr`, `ptt.hs01.kep.tr` vb.) geçerlilik denetimi (`validate_kep_address`).
   - KEP tebligat paketi simülasyonu ile SHA-256 sözleşme parmak izi, **Mazbata Barkodu** (`DELIL-2026-TR-XXXXX`) ve KEP İleti ID üretimi.

5. **Satın Alma Yönetim Paneli (`/admin`):**
   - Teklif filtreleme ve süreç takibi: *Teklif Alındı*, *Teknik İncelemede*, *Pazarlık / Revize İstendi*, *Kabul Edildi (Sipariş Verildi)*, *Kabul Edildi (KEP ile Tebliğ Edildi)*, *Reddedildi*.
   - **Alıcı & KEP Ayarları:** Şirket unvanı, VKN, KEP adresi ve yetkili kişi bilgilerini SQLite üzerinden yönetme.
   - UBL XML, A4 Sözleşme ve A4 Karşılaştırma Raporuna hızlı erişim butonları.

6. **Sıfır Bağımlılık (Zero-Dependency) Çoklu Dağıtım:**
   - **Python:** Standart kütüphaneler ve yerleşik SQLite ile doğrudan çalışır (`server.py`).
   - **Docker:** İzole ve üretime hazır konteyner imajı.
   - **PHP / cPanel:** Paylaşımlı sunucular için hazır JSON REST backend (`api.php`).
   - **Offline Mod:** İnternetsiz tarayıcı yerel hafızası (`localStorage`) desteği.

---

## 🚀 Hızlı Başlangıç ve Kurulum

### Yöntem 1: Python ile Çalıştırma (Önerilen)

Harici `pip` bağımlılığı bulunmamaktadır:

```bash
git clone https://github.com/eimza-kep/kobi-tedarikci-teklif-toplama-scripti.git
cd kobi-tedarikci-teklif-toplama-scripti

python server.py
```

- **Tedarikçi Teklif Verme Portalı:** [http://localhost:8090](http://localhost:8090)
- **Satın Alma Yönetim Paneli:** [http://localhost:8090/admin](http://localhost:8090/admin)
- **Sağlık Kontrolü:** [http://localhost:8090/health](http://localhost:8090/health)

*(Windows kullanıcıları klasördeki **`Baslat.bat`**, Linux/macOS kullanıcıları **`./baslat.sh`** dosyasına çift tıklayabilir).*

---

### Yöntem 2: Docker ile Çalıştırma

```bash
docker build -t kobi-rfq .
docker run -d -p 8090:8090 -v $(pwd)/data:/app/data --name kobi-rfq-app kobi-rfq
```

---

### Yöntem 3: PHP / Paylaşımlı Hosting (cPanel)

Dosyaları sunucunuzdaki `public_html/teklif/` dizinine yükleyin. `api.php` otomatik olarak JSON veritabanını oluşturup yönetecektir.

---

## 🔌 REST API Uç Noktaları

| Metot | Uç Nokta | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/api/teklifler` | Tüm gelen tedarikçi tekliflerini JSON listesi olarak döner. |
| `POST` | `/api/teklif-ver` | Yeni tedarikçi teklifini kaydeder, `tracking_code` üretir. |
| `GET` | `/api/karsilastirma-matrisi?rfq_ref=...` | Talep referansına göre teklifleri puanlar ve JSON matrisini döner. |
| `GET` | `/api/karsilastirma-raporu-html?rfq_ref=...` | Yazdırılabilir / PDF formatında A4 Karşılaştırma ve Komisyon Karar Raporu üretir. |
| `GET` | `/api/karsilastirma-raporu-csv?rfq_ref=...` | Excel uyumlu UTF-8 with BOM formatında CSV karşılaştırma dökümü indirir. |
| `GET` | `/api/export-order-xml?tracking_code=...` | GİB UBL-TR 2.1 Satın Alma Sipariş Fişi (`Order XML`) dosyasını indirir. |
| `GET` | `/api/satin-alma-sozlesmesi?tracking_code=...` | Resmi A4 formatında Satın Alma Sözleşmesi HTML çıktısını üretir. |
| `POST` | `/api/kep-gonder` | Tedarikçi KEP adresine resmi sipariş tebliği paketi ve mazbata üretir. |
| `GET` | `/api/kabul-eposta?tracking_code=...` | Tedarikçiye iletilecek onay e-posta metnini döner. |
| `POST` | `/api/kep-dogrula` | KEP adresinin formatını ve sağlayıcı geçerliliğini denetler. |
| `POST` | `/api/durum-guncelle` | Teklif durumunu günceller. |
| `GET` | `/api/ayarlar` | Alıcı firma ve KEP ayarlarını döner. |
| `POST` | `/api/ayarlar` | Alıcı firma ve KEP ayarlarını kaydeder. |
| `GET` | `/health` | Servis durum kontrolü (`status: ok`). |

---

## 🧪 Testleri Çalıştırma

Tüm teklif kayıtları, karşılaştırma matrisi puanlama motoru, UBL-TR 2.1 XML üretimi, KEP adresi doğrulayıcı ve sözleşme şablonları otomatik birim testleriyle korunmaktadır:

```bash
python scripts/test_teklif.py
```

Çıktı:
```text
============================================================
  KOBİ TEDARİKÇİ TEKLİF & KEP SÖZLEŞME TEST SÜİTİ
============================================================
test_acceptance_email_generator ... ok
test_buyer_settings ... ok
test_comparison_matrix_html_and_csv ... ok
test_database_columns_and_migration ... ok
test_database_table_exists ... ok
test_files_exist ... ok
test_kep_address_validator ... ok
test_kep_transmission_package ... ok
test_purchase_order_contract_and_html ... ok
test_quote_insert_and_retrieve ... ok
test_quote_status_update ... ok
test_rfq_comparison_matrix_and_discount ... ok
test_ubl_tr_order_xml_generation ... ok
test_ubl_tr_order_xml_multi_items ... ok

----------------------------------------------------------------------
Ran 14 tests in 0.018s

OK
✅ TÜM BİRİM VE ENTEGRASYON TESTLERİ BAŞARIYLA GEÇTİ!
```

---

## 🌐 KOBİ & E-Dönüşüm Açık Kaynak Ekosistemi

Bu satın alma ve tedarikçi teklif toplama aracı, [@eimza-kep](https://github.com/eimza-kep) açık kaynak ekosisteminin B2B tedarik yönetimi bileşenidir. İlgili diğer araçlar:

* 💼 [kobi-hizli-teklif-scripti](https://github.com/eimza-kep/kobi-hizli-teklif-scripti) - Kendi müşterilerinize yönelik hızlı satış teklifi hazırlama motoru.
* 🏢 [kobi-finans-yonetim-excel-sablonlari](https://github.com/eimza-kep/kobi-finans-yonetim-excel-sablonlari) - Satın alma bütçesi, nakit akışı ve stok takip şablonları.
* 📄 [e-fatura-xml-goruntuleyici](https://github.com/eimza-kep/e-fatura-xml-goruntuleyici) - Tedarikçilerden gelen e-Fatura XML dosyalarını görüntüleme ve KDV kontrolü.
* 🌟 [awesome-turkiye-e-donusum](https://github.com/eimza-kep/awesome-turkiye-e-donusum) - Türkiye e-Dönüşüm açık kaynak araçları ve kütüphaneleri kürasyonu.

---

## ⚖️ Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak sunulmuştur. Kurumsal ve ticari amaçlarla tamamen serbestçe kullanılabilir.
