# 📊 KOBİ Tedarikçi Teklif Toplama, Karşılaştırma Matrisi & KEP Satın Alma Portalı

[![CI Test Suite](https://github.com/eimza-kep/kobi-tedarikci-teklif-toplama-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kobi-tedarikci-teklif-toplama-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kobi-tedarikci-teklif-toplama-scripti/)
[![KEP Destekli](https://img.shields.io/badge/KEP%20S%C3%B6zle%C5%9Fme-TTK%2018%2F3-blue.svg)](#)
[![Karşılaştırma](https://img.shields.io/badge/RFQ%20Analiz-Matris%20Puanlama-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)

KOBİ'ler, şirketler, fabrikalar ve satın alma departmanları için; tedarikçilerden gelen fiyat tekliflerini (RFQ - Request for Quotation) tek bir havuzda toplayan, **en uygun fiyat ve vade karşılaştırma matrisi sunan**, **Türk Ticaret Kanunu (TTK m. 18/3) uyumlu Resmi Satın Alma Sözleşmesi üreten** ve **KEP (Kayıtlı Elektronik Posta) üzerinden resmi sipariş tebliği yapan** açık kaynaklı kurumsal satın alma yazılımı.

---

## 🎯 Temel Yetenekler & Özellikler

1. **Tedarikçi Karşılaştırma Matrisi ve En Uygun Teklif Analizi:**
   - Aynı satınalma talebine veya kategoriye ait teklifleri tek ekranda yan yana karşılaştırır.
   - Çok kriterli ağırlıklı puanlama motoru: **Fiyat (%45)**, **Ödeme Vadesi (%25)**, **Teslimat Süresi (%20)** ve **Nakliye Şartları (%10)**.
   - En iyi teklife **🏆 En Avantajlı Teklif**, en ucuz teklife **🏷️ En Düşük Fiyat** ve en süratli teklife **⚡ En Hızlı Teslimat** rozetleri atar.
   - Tek tıkla tedarikçiye gönderilmek üzere hazırlanmış **Resmi Kabul E-Postası Şablonu**.

2. **KEP Üzerinden Resmi Satın Alma Sözleşmesi (TTK m. 18/3):**
   - Teklif kabul edildiğinde resmi A4 formatında yazdırılabilir / PDF kaydedilebilir **Satın Alma Sözleşmesi** üretir.
   - Tedarikçi KEP adresi (`firma@hs01.kep.tr`, `ptt.hs01.kep.tr` vb.) geçerlilik denetimi (`validate_kep_address`).
   - KEP tebligat paketi simülasyonu ile SHA-256 sözleşme parmak izi, **Mazbata Barkodu** (`DELIL-2026-TR-XXXXX`) ve KEP İleti ID üretimi.

3. **Kapsamlı Tedarikçi Teklif Formu:**
   - Tedarikçi unvanı, VKN/TCKN, KEP adresi, iletişim yetkilisi, ihale/şartname referansı.
   - Tutar, para birimi (TRY, USD, EUR), vade (peşin, 30/60/90 gün), teslimat süresi, opsiyon geçerlilik tarihi ve Incoterms teslim şekli (DDP, Ex-Works).
   - Resmi teklif dökümü (`TEKLIF-2026-XXXX`).

4. **Satın Alma Yönetim Paneli (`/admin`):**
   - Teklif filtreleme ve süreç takibi: *Teklif Alındı*, *Teknik İncelemede*, *Pazarlık / Revize İstendi*, *Kabul Edildi (Sipariş Verildi)*, *Kabul Edildi (KEP ile Tebliğ Edildi)*, *Reddedildi*.
   - **Alıcı & KEP Ayarları:** Şirket unvanı, VKN, KEP adresi ve yetkili kişi bilgilerini SQLite üzerinden yönetme.
   - Excel uyumlu UTF-8 BOM destekli tek tıkla **CSV Dışa Aktarımı**.

5. **Sıfır Bağımlılık (Zero-Dependency) Çoklu Dağıtım:**
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
| `GET` | `/api/karsilastirma-matrisi?rfq_ref=...` | Talep referansına göre teklifleri puanlar ve en avantajlı teklifi döner. |
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

Tüm teklif kayıtları, karşılaştırma matrisi puanlama motoru, KEP adresi doğrulayıcı ve sözleşme şablonları otomatik birim testleriyle korunmaktadır:

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
test_database_table_exists ... ok
test_files_exist ... ok
test_kep_address_validator ... ok
test_kep_transmission_package ... ok
test_purchase_order_contract_and_html ... ok
test_quote_insert_and_retrieve ... ok
test_quote_status_update ... ok
test_rfq_comparison_matrix ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.018s

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
