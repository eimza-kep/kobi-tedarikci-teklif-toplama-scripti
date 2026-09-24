# KOBİ Tedarikçi Teklif Toplama ve Satın Alma Portalı

[![CI Test Suite](https://github.com/eimza-kep/kobi-tedarikci-teklif-toplama-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kobi-tedarikci-teklif-toplama-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kobi-tedarikci-teklif-toplama-scripti/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![PHP: 7.4+](https://img.shields.io/badge/PHP-7.4%2B-purple.svg)](https://php.net)

KOBİ'ler, şirketler, fabrikalar ve satın alma departmanları için; tedarikçilerden gelen fiyat tekliflerini (RFQ - Request for Quotation) tek bir merkezde toplayan, **resmi teklif ve ihale katılım belgesi basan**, **vade ve fiyat karşılaştırması sunan** açık kaynaklı kurumsal satın alma yazılımı.

---

## 🎯 Temel Yetenekler

- **Tedarikçi RFQ Portalı:** Tedarikçi firma unvanı, VKN, yetkili bilgileri, teklif kategorisi, şartname referansı.
- **Ticari Şartlar:** Toplam tutar (KDV hariç), para birimi seçimi (TRY, USD, EUR), ödeme vadesi (peşin, 30/60/90 gün), teslimat süresi, opsiyon geçerlilik tarihi ve nakliye teslim şekli (DDP, Ex-Works).
- **Resmi Teklif Formu Çıktısı:** Takip numaralı (`TEKLIF-2026-XXXX`) ve imza bloklu yazdırılabilir veya PDF olarak saklanabilir kurumsal teklif evrakı üretir.
- **Satın Alma Yönetim Paneli (`/admin`):**
  - Gelen tüm tekliflerin kategorilere ve vadelere göre karşılaştırılması.
  - Teklif durum yönetimi: "Teklif Alındı", "Teknik İncelemede", "Pazarlık / Revize İstendi", "Kabul Edildi (Sipariş Verildi)", "Reddedildi".
  - Toplam teklif hacmi ve analitik metrikler.
  - Excel uyumlu UTF-8 BOM destekli tek tıkla **CSV Dışa Aktarımı**.
- **Sıfır Bağımlılık (Zero-Dependency):**
  - **Python Motoru:** Dahili SQLite veritabanı ile tek tıkla lokalde veya sunucuda çalışır (`server.py`).
  - **PHP Motoru:** Paylaşımlı hosting ve cPanel için hazır JSON REST backend (`api.php`).
  - **Offline Mod:** İnternetsiz çalışma ve tarayıcı yerel hafızası (`localStorage`) desteği.

---

## 🚀 Hızlı Başlangıç

### Windows (Tek Tıkla Çalıştır)
1. Repoyu klonlayın veya indirin.
2. `Baslat.bat` dosyasına çift tıklayın.
3. Otomatik olarak açılır:
   - Tedarikçi Teklif Formu: `http://localhost:8090`
   - Satın Alma Paneli: `http://localhost:8090/admin`

### Linux & macOS
```bash
git clone https://github.com/eimza-kep/kobi-tedarikci-teklif-toplama-scripti.git
cd kobi-tedarikci-teklif-toplama-scripti
chmod +x baslat.sh
./baslat.sh
```

### PHP / Paylaşımlı Hosting
Dosyaları sunucunuzdaki `/teklif/` veya `/satin-alma/` dizinine yükleyin. `api.php` otomatik olarak JSON veritabanını oluşturup yönetecektir.

---

## 📊 Mimari ve Dosya Yapısı

```
kobi-tedarikci-teklif-toplama-scripti/
├── index.html              # Tedarikçi teklif verme formu ve teklif çıktısı
├── admin.html              # Satın alma değerlendirme ve karşılaştırma paneli
├── server.py               # Standalone Python SQLite HTTP sunucusu (Port 8090)
├── api.php                 # PHP tabanlı REST backend
├── Baslat.bat              # Windows tek tıkla başlatıcı
├── baslat.sh               # Linux / macOS başlatıcı
├── scripts/
│   └── test_teklif.py      # Otomatik test paketi
├── .github/
│   └── workflows/ci.yml    # GitHub Actions CI testi
└── README.md               # Dokümantasyon
```

---

## 🧪 Testleri Çalıştırma

```bash
python scripts/test_teklif.py
```

---

## ⚖️ Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak sunulmuştur.
