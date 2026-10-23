# -*- coding: utf-8 -*-
"""
scripts/rfq_comparison_engine.py
--------------------------------
Tedarikçi teklif karşılaştırma matrisi, fiyat/vade/teslimat/iskonto puanlama motoru,
yazdırılabilir A4 Karşılaştırma Raporu (HTML), Excel CSV ihracı ve
tedarikçi kabul bildirim e-postası şablon üreticisi.
"""

import datetime
from xml.sax.saxutils import escape

DEFAULT_BUYER = {
    "title": "KOBİ DİJİTAL DÖNÜŞÜM VE TEDARİK A.Ş.",
    "vkn": "5810492810",
    "tax_office": "Büyük Mükellefler V.D.",
    "address": "Bilişim Vadisi, Teknoloji Blokları No:42/A",
    "city": "İstanbul",
    "phone": "0850 300 40 50",
    "email": "satinalma@kobisirket.com.tr",
    "authorized_person": "Satın Alma Komisyonu"
}

def score_payment_terms(term_text, has_cash_discount=False):
    """
    Ödeme vadesine göre puanlama (0 - 30 puan).
    Uzun vade ve esnek ödeme alıcı nakit akışı için daha yüksek puan alır.
    Erken ödeme / peşin iskontosu sunulmuşsa ek avantaj puanı eklenir.
    """
    t = str(term_text).lower()
    base_score = 10
    if "90" in t:
        base_score = 30
    elif "60" in t:
        base_score = 25
    elif "30" in t:
        base_score = 18
    elif "kısmi" in t or "avans" in t:
        base_score = 12
    elif "peşin" in t:
        base_score = 10 if has_cash_discount else 5
    else:
        base_score = 10

    if has_cash_discount:
        base_score = min(30, base_score + 5)

    return base_score

def score_shipping_terms(ship_text):
    """
    Nakliye şartına göre puanlama (0 - 15 puan).
    DDP (adrese teslim) en yüksek puanı alır.
    """
    s = str(ship_text).lower()
    if "ddp" in s or "satıcı" in s or "adrese teslim" in s:
        return 15
    if "ex-works" in s or "fabrika" in s:
        return 5
    if "alıcı ödemeli" in s:
        return 8
    return 10

def analyze_rfq_group(quotes):
    """
    Aynı RFQ veya kategoriye ait teklifleri karşılaştırır;
    fiyat, iskonto, vade ve teslimat süresine göre skorlar;
    'En Avantajlı Teklif', 'En Düşük Fiyat', 'En Hızlı Teslimat' rozetlerini atar.
    """
    if not quotes:
        return []

    # Geçerli tutarları ve teslimat sürelerini topla
    valid_amounts = []
    valid_days = []

    for q in quotes:
        amt = float(q.get("total_amount", 0))
        disc = float(q.get("discount_amount", 0))
        net_amt = max(0.0, amt - disc)
        if net_amt > 0:
            valid_amounts.append(net_amt)
        elif amt > 0:
            valid_amounts.append(amt)

        d = int(q.get("delivery_days", 1))
        if d > 0:
            valid_days.append(d)

    min_amount = min(valid_amounts) if valid_amounts else 0.0
    max_amount = max(valid_amounts) if valid_amounts else 0.0
    min_days = min(valid_days) if valid_days else 1
    max_days = max(valid_days) if valid_days else 1

    scored_quotes = []

    for q in quotes:
        item = dict(q)
        gross_amount = float(item.get("total_amount", 0))
        discount_amount = float(item.get("discount_amount", 0))
        discount_rate = float(item.get("discount_rate", 0))

        if discount_rate > 0 and discount_amount == 0 and gross_amount > 0:
            discount_amount = round(gross_amount * (discount_rate / 100.0), 2)
            item["discount_amount"] = discount_amount

        net_amount = max(0.0, gross_amount - discount_amount)
        item["net_amount"] = net_amount
        days = int(item.get("delivery_days", 1))

        # 1. Fiyat Puanı (0 - 45 puan) - Net tutar baz alınır
        if max_amount > min_amount and net_amount > 0:
            price_score = 45.0 * (1.0 - (net_amount - min_amount) / (max_amount - min_amount))
        else:
            price_score = 45.0

        # İskonto Teşvik Bonusu (0 - 5 puan)
        has_cash_discount = ("peşin" in str(item.get("payment_terms", "")).lower() and discount_amount > 0)
        discount_bonus = 0.0
        if discount_amount > 0 and gross_amount > 0:
            discount_pct = (discount_amount / gross_amount) * 100.0
            discount_bonus = min(5.0, discount_pct * 0.5)

        # 2. Teslimat Hızı Puanı (0 - 20 puan)
        if max_days > min_days and days > 0:
            delivery_score = 20.0 * (1.0 - (days - min_days) / (max_days - min_days))
        else:
            delivery_score = 20.0

        # 3. Vade Puanı (0 - 25 puan)
        term_score = score_payment_terms(item.get("payment_terms", ""), has_cash_discount=has_cash_discount)

        # 4. Nakliye Puanı (0 - 10 puan)
        ship_score = score_shipping_terms(item.get("shipping_terms", ""))

        total_score = round(
            price_score + delivery_score + (term_score * 25.0 / 30.0) + (ship_score * 10.0 / 15.0) + discount_bonus,
            1
        )
        total_score = min(100.0, total_score)

        item["score"] = total_score
        item["is_lowest_price"] = (net_amount == min_amount and net_amount > 0)
        item["is_fastest_delivery"] = (days == min_days and days > 0)
        item["has_discount"] = (discount_amount > 0)
        item["is_best_value"] = False
        scored_quotes.append(item)

    # En yüksek puanı alan teklifi bul
    if scored_quotes:
        best_quote = max(scored_quotes, key=lambda x: x["score"])
        best_quote["is_best_value"] = True

    # Puana göre çoktan aza sırala
    scored_quotes.sort(key=lambda x: x["score"], reverse=True)
    return scored_quotes

def generate_acceptance_email(quote, buyer_company=None):
    """
    Seçilen tedarikçiye gönderilecek resmi satın alma kabul bildirim e-postası şablonu.
    """
    comp_title = (buyer_company or DEFAULT_BUYER).get("title", "KOBİ Satın Alma Direktörlüğü")
    comp_contact = (buyer_company or DEFAULT_BUYER).get("contact_person", "Satın Alma Komisyonu")
    comp_phone = (buyer_company or DEFAULT_BUYER).get("phone", "0850 300 40 50")
    comp_email = (buyer_company or DEFAULT_BUYER).get("email", "satinalma@sirketiniz.com")

    tracking_code = quote.get("tracking_code", "TEKLIF-2026-0001")
    supplier_name = quote.get("supplier_name", "Tedarikçi Firma")
    amount = float(quote.get("total_amount", 0))
    discount = float(quote.get("discount_amount", 0))
    net_amount = amount - discount if discount > 0 else amount
    currency = quote.get("currency", "TRY (₺)")
    terms = quote.get("payment_terms", "Vadeli")
    days = quote.get("delivery_days", 7)
    ref = quote.get("rfq_ref") or quote.get("rfq_category") or "Satın Alma İhalesi"

    subject = f"Sipariş Onayı ve Teklif Kabul Bildirimi (Ref: {tracking_code} / {ref})"

    discount_line = f"Uygulanan İskonto          : -{discount:,.2f} {currency}\nNet Sipariş Tutarı         : {net_amount:,.2f} {currency} + KDV\n" if discount > 0 else ""

    body = f"""Sayın {supplier_name} Yetkilileri,

Şirketimize '{tracking_code}' takip referans numarası ile iletmiş olduğunuz '{ref}' konulu fiyat teklifiniz, Satın Alma Komisyonumuz tarafından incelenmiş ve en uygun teklif olarak KABUL EDİLMİŞTİR.

SİPARİŞ VE ANLAŞMA DETAYLARI:
--------------------------------------------------
Teklif / Sipariş Referansı : {tracking_code}
İlgili Talep / Şartname    : {ref}
Kabul Edilen Brüt Tutar    : {amount:,.2f} {currency}
{discount_line}Ödeme Vadesi ve Koşulları  : {terms}
Taahhüt Edilen Teslimat    : {days} İş Günü
Teslim Şekli               : {quote.get('shipping_terms', 'DDP')}
--------------------------------------------------

Sözleşme ve sipariş teyit yazımız hazırlanmış olup, kayıtlı KEP (Kayıtlı Elektronik Posta) adresinize resmi olarak tebliğ edilecektir. 
GİB UBL-TR 2.1 Satın Alma Sipariş Fişi (Order XML) sistemimizde oluşturulmuştur.

Lütfen sipariş hazırlık sürecini başlatarak sevkiyat takvimi hakkında tarafımızı bilgilendiriniz.

İyi çalışmalar dileriz.

Saygılarımızla,
{comp_title}
Yetkili: {comp_contact}
Tel: {comp_phone}
E-Posta: {comp_email}
"""
    return {
        "subject": subject,
        "body": body,
        "supplier_email": quote.get("supplier_email", "")
    }

def generate_comparison_matrix_html(rfq_ref, quotes, buyer_company=None):
    """
    A4 formatında yazdırılabilir ve PDF olarak saklanabilir
    Tedarikçi Teklif Karşılaştırma ve İhale Değerlendirme Raporu (HTML).
    """
    buyer = buyer_company or DEFAULT_BUYER
    analyzed = analyze_rfq_group(quotes)
    today_str = datetime.date.today().strftime("%d.%m.%Y")
    ref_title = rfq_ref if rfq_ref else "Tüm Teklifler Genel Karşılaştırma"

    total_quotes = len(analyzed)
    min_price = min([q.get("net_amount", float(q.get("total_amount", 0))) for q in analyzed]) if analyzed else 0.0
    avg_price = (sum([q.get("net_amount", float(q.get("total_amount", 0))) for q in analyzed]) / total_quotes) if total_quotes > 0 else 0.0
    min_delivery = min([int(q.get("delivery_days", 1)) for q in analyzed]) if analyzed else 0

    rows_html = []
    for rank, q in enumerate(analyzed, start=1):
        gross = float(q.get("total_amount", 0))
        disc = float(q.get("discount_amount", 0))
        net = q.get("net_amount", gross - disc)
        vat = net * 0.20
        total_with_vat = net + vat
        currency = q.get("currency", "TRY")
        score = q.get("score", 0)

        badges = []
        if q.get("is_best_value"):
            badges.append('<span class="badge badge-best">🥇 En Avantajlı Teklif</span>')
        if q.get("is_lowest_price"):
            badges.append('<span class="badge badge-price">💰 En Uygun Fiyat</span>')
        if q.get("is_fastest_delivery"):
            badges.append('<span class="badge badge-speed">⚡ En Hızlı Teslim</span>')
        if q.get("has_discount"):
            badges.append(f'<span class="badge badge-disc">🏷️ %{disc/gross*100:.1f} İskonto</span>' if gross > 0 else '<span class="badge badge-disc">🏷️ İskontolu</span>')

        badge_block = " ".join(badges) if badges else '<span style="color:#64748b; font-size:0.8rem;">-</span>'

        disc_td = f"-{disc:,.2f} {currency}" if disc > 0 else "0.00"

        rows_html.append(f"""
        <tr class="{'winner-row' if q.get('is_best_value') else ''}">
            <td style="text-align: center; font-weight: bold;">{rank}</td>
            <td>
                <b>{escape(str(q.get('supplier_name', 'Tedarikçi')))}</b><br>
                <small style="color: #64748b;">VKN: {escape(str(q.get('supplier_vkn', '-')))} | Ref: {escape(str(q.get('tracking_code', '-')))}</small><br>
                <div style="margin-top: 4px;">{badge_block}</div>
            </td>
            <td style="text-align: right;">{gross:,.2f} {currency}</td>
            <td style="text-align: right; color: #dc2626;">{disc_td}</td>
            <td style="text-align: right; font-weight: bold; color: #0284c7;">{net:,.2f} {currency}</td>
            <td style="text-align: right; font-weight: bold;">{total_with_vat:,.2f} {currency}</td>
            <td>{escape(str(q.get('payment_terms', '-')))}</td>
            <td style="text-align: center;"><b>{q.get('delivery_days', 1)}</b> Gün</td>
            <td>{escape(str(q.get('shipping_terms', 'DDP')))}</td>
            <td style="text-align: center; font-weight: 800; font-size: 1.05rem; color: #1e3a8a;">{score} / 100</td>
            <td style="text-align: center;">
                <span class="status-pill status-{'approved' if 'Kabul' in str(q.get('status','')) else 'pending'}">{escape(str(q.get('status', 'İnceleniyor')))}</span>
            </td>
        </tr>
        """)

    tbody_content = "\n".join(rows_html)

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Satın Alma Teklif Karşılaştırma Raporu - {escape(ref_title)}</title>
<style>
  * {{ box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  body {{ background: #f8fafc; padding: 24px 16px; color: #0f172a; margin: 0; }}
  .toolbar {{ max-width: 1100px; margin: 0 auto 16px auto; display: flex; justify-content: space-between; align-items: center; background: white; padding: 12px 20px; border-radius: 8px; border: 1px solid #cbd5e1; }}
  .report-container {{ max-width: 1100px; margin: auto; background: white; border: 1px solid #cbd5e1; padding: 32px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.03); }}
  .report-header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #0f172a; padding-bottom: 16px; margin-bottom: 20px; }}
  .header-left h1 {{ margin: 0; font-size: 1.35rem; color: #0f172a; text-transform: uppercase; font-weight: 800; }}
  .header-left p {{ margin: 4px 0 0 0; color: #64748b; font-size: 0.9rem; }}
  .header-right {{ text-align: right; font-size: 0.85rem; color: #334155; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }}
  .stat-card {{ background: #f1f5f9; border-radius: 6px; padding: 12px 14px; border-left: 4px solid #2563eb; }}
  .stat-label {{ font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: 700; }}
  .stat-value {{ font-size: 1.15rem; font-weight: 800; color: #0f172a; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 0.86rem; }}
  th, td {{ border: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; vertical-align: middle; }}
  th {{ background: #0f172a; color: white; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; }}
  tr:nth-child(even) {{ background: #f8fafc; }}
  tr.winner-row {{ background: #f0fdf4 !important; border: 2px solid #16a34a; }}
  .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; margin-right: 4px; }}
  .badge-best {{ background: #dcfce7; color: #15803d; border: 1px solid #86efac; }}
  .badge-price {{ background: #dbeafe; color: #1d4ed8; border: 1px solid #93c5fd; }}
  .badge-speed {{ background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }}
  .badge-disc {{ background: #fce7f3; color: #be185d; border: 1px solid #fbcfe8; }}
  .status-pill {{ padding: 3px 8px; border-radius: 999px; font-size: 0.72rem; font-weight: bold; display: inline-block; }}
  .status-approved {{ background: #dcfce7; color: #166534; }}
  .status-pending {{ background: #f1f5f9; color: #475569; }}
  .signatures-section {{ margin-top: 40px; padding-top: 20px; border-top: 1px dashed #cbd5e1; display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center; }}
  .sig-box {{ border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px 10px; background: #fafafa; font-size: 0.85rem; }}
  .sig-space {{ height: 45px; }}
  @media print {{
    body {{ background: transparent; padding: 0; }}
    .toolbar {{ display: none !important; }}
    .report-container {{ border: none; padding: 0; box-shadow: none; max-width: 100%; }}
  }}
</style>
</head>
<body>

<div class="toolbar">
  <span style="font-weight: 700; font-size: 0.95rem;">📊 Tedarikçi Teklif Karşılaştırma ve İhale Raporu</span>
  <div style="display: flex; gap: 8px;">
    <a href="/api/karsilastirma-raporu-csv?rfq_ref={escape(rfq_ref)}" style="background: #10b981; color: white; text-decoration: none; padding: 8px 14px; border-radius: 6px; font-weight: bold; font-size: 0.85rem;">📥 Excel CSV İndir</a>
    <button onclick="window.print()" style="background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 0.85rem;">🖨️ Yazdır / PDF Kaydet</button>
  </div>
</div>

<div class="report-container">
  <div class="report-header">
    <div class="header-left">
      <h1>SATIN ALMA TEKLİF KARŞILAŞTIRMA VE KOMİSYON KARAR RAPORU</h1>
      <p>Talep / İhale Ref: <b>{escape(ref_title)}</b> | Rapor Tarihi: {today_str}</p>
    </div>
    <div class="header-right">
      <b>{escape(buyer.get('title', 'KOBİ'))}</b><br>
      VKN: {escape(buyer.get('vkn', '5810492810'))}<br>
      {escape(buyer.get('city', 'İstanbul'))}
    </div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Toplam Teklif Sayısı</div>
      <div class="stat-value">{total_quotes} Firma</div>
    </div>
    <div class="stat-card" style="border-left-color: #10b981;">
      <div class="stat-label">En Düşük Teklif (Net)</div>
      <div class="stat-value">{min_price:,.2f} TRY</div>
    </div>
    <div class="stat-card" style="border-left-color: #f59e0b;">
      <div class="stat-label">Ortalama Teklif</div>
      <div class="stat-value">{avg_price:,.2f} TRY</div>
    </div>
    <div class="stat-card" style="border-left-color: #8b5cf6;">
      <div class="stat-label">En Hızlı Teslimat</div>
      <div class="stat-value">{min_delivery} İş Günü</div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width: 35px; text-align: center;">Sıra</th>
        <th>Tedarikçi Bilgisi</th>
        <th style="text-align: right;">Brüt Tutar</th>
        <th style="text-align: right;">İskonto</th>
        <th style="text-align: right;">Net (KDV Hariç)</th>
        <th style="text-align: right;">KDV Dahil Toplam</th>
        <th>Ödeme Vadesi</th>
        <th style="text-align: center;">Teslimat</th>
        <th>Teslim Şekli</th>
        <th style="text-align: center;">Puan (100)</th>
        <th style="text-align: center;">Durum</th>
      </tr>
    </thead>
    <tbody>
      {tbody_content}
    </tbody>
  </table>

  <div style="font-size: 0.82rem; color: #475569; line-height: 1.5; margin-bottom: 20px; background: #f8fafc; padding: 12px; border-left: 3px solid #2563eb; border-radius: 4px;">
    <b>DEĞERLENDİRME KRİTERLERİ VE HESAPLAMA METODOLOJİSİ:</b><br>
    • Fiyat Ağırlığı: 45 Puan (Net tutara göre normalize edilmiştir)<br>
    • Vade ve Nakit Akışı Ağırlığı: 25 Puan (60-90 gün vadeli teklifler ve erken ödeme iskontosu teşvik edilir)<br>
    • Teslimat Süresi Ağırlığı: 20 Puan (En erken teslimat yapan teklif maksimum puanı alır)<br>
    • Nakliye ve Lojistik Şartı: 10 Puan (DDP adrese teslim koşulu 10 tam puanla değerlendirilir)
  </div>

  <div class="signatures-section">
    <div class="sig-box">
      <b>Satın Alma Uzmanı</b><br>
      İnceleme ve Karşılaştırma<br>
      <div class="sig-space"></div>
      İmza / Tarih
    </div>
    <div class="sig-box">
      <b>Mali İşler Direktörü</b><br>
      Bütçe ve Vade Uygunluğu<br>
      <div class="sig-space"></div>
      İmza / Tarih
    </div>
    <div class="sig-box">
      <b>Genel Müdür / Onay Makamı</b><br>
      Sipariş ve Sözleşme Onayı<br>
      <div class="sig-space"></div>
      İmza / Tarih
    </div>
  </div>
</div>

</body>
</html>"""

def generate_comparison_matrix_csv(rfq_ref, quotes):
    """
    Excel uyumlu UTF-8 with BOM formatında CSV karşılaştırma raporu çıktısı üretir.
    """
    analyzed = analyze_rfq_group(quotes)
    lines = [
        "Sira;Takip Kodu;Tedarikci Adi;VKN;Brut Tutar;Iskonto;Net Tutar;Para Birimi;Odeme Vadesi;Teslimat Gunu;Teslim Sekli;Puan;Durum;Rozetler"
    ]

    for rank, q in enumerate(analyzed, start=1):
        gross = float(q.get("total_amount", 0))
        disc = float(q.get("discount_amount", 0))
        net = q.get("net_amount", gross - disc)
        currency = str(q.get("currency", "TRY")).replace(";", " ")
        badges = []
        if q.get("is_best_value"):
            badges.append("En Avantajli")
        if q.get("is_lowest_price"):
            badges.append("En Dusuk Fiyat")
        if q.get("is_fastest_delivery"):
            badges.append("En Hizli Teslimat")
        if q.get("has_discount"):
            badges.append("Iskontolu")

        badge_str = " | ".join(badges) if badges else "-"
        supplier = str(q.get("supplier_name", "")).replace(";", " ")
        vkn = str(q.get("supplier_vkn", ""))
        code = str(q.get("tracking_code", ""))
        terms = str(q.get("payment_terms", "")).replace(";", " ")
        shipping = str(q.get("shipping_terms", "")).replace(";", " ")
        status = str(q.get("status", "")).replace(";", " ")
        score = str(q.get("score", 0))
        days = str(q.get("delivery_days", 1))

        row = f'{rank};"{code}";"{supplier}";"{vkn}";{gross:.2f};{disc:.2f};{net:.2f};"{currency}";"{terms}";{days};"{shipping}";{score};"{status}";"{badge_str}"'
        lines.append(row)

    # UTF-8 BOM ekle (\ufeff)
    return "\ufeff" + "\n".join(lines)
