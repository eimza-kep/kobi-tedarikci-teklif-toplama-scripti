# -*- coding: utf-8 -*-
"""
scripts/rfq_comparison_engine.py
--------------------------------
Tedarikçi teklif karşılaştırma matrisi, fiyat/vade/teslimat puanlama motoru
ve tedarikçi kabul bildirim e-postası şablon üreticisi.
"""

def score_payment_terms(term_text):
    """
    Ödeme vadesine göre puanlama (0 - 30 puan).
    Uzun vade ve esnek ödeme alıcı için daha yüksek puan alır.
    """
    t = str(term_text).lower()
    if "90" in t:
        return 30
    if "60" in t:
        return 25
    if "30" in t:
        return 18
    if "kısmi" in t or "avans" in t:
        return 12
    if "peşin" in t:
        return 5
    return 10

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
    Aynı RFQ veya kategoriye ait teklifleri karşılaştırır,
    fiyat, vade ve teslimat süresine göre skorlar,
    'En Avantajlı Teklif' ve 'En Düşük Fiyat' rozetlerini atar.
    """
    if not quotes:
        return []

    # Geçerli tutarları ve teslimat sürelerini topla
    valid_amounts = [float(q.get("total_amount", 0)) for q in quotes if float(q.get("total_amount", 0)) > 0]
    valid_days = [int(q.get("delivery_days", 1)) for q in quotes if int(q.get("delivery_days", 1)) > 0]

    min_amount = min(valid_amounts) if valid_amounts else 0.0
    max_amount = max(valid_amounts) if valid_amounts else 0.0
    min_days = min(valid_days) if valid_days else 1
    max_days = max(valid_days) if valid_days else 1

    scored_quotes = []

    for q in quotes:
        item = dict(q)
        amount = float(item.get("total_amount", 0))
        days = int(item.get("delivery_days", 1))

        # 1. Fiyat Puanı (0 - 45 puan)
        if max_amount > min_amount and amount > 0:
            price_score = 45.0 * (1.0 - (amount - min_amount) / (max_amount - min_amount))
        else:
            price_score = 45.0

        # 2. Teslimat Hızı Puanı (0 - 20 puan)
        if max_days > min_days and days > 0:
            delivery_score = 20.0 * (1.0 - (days - min_days) / (max_days - min_days))
        else:
            delivery_score = 20.0

        # 3. Vade Puanı (0 - 25 puan)
        term_score = score_payment_terms(item.get("payment_terms", ""))

        # 4. Nakliye Puanı (0 - 10 puan)
        ship_score = score_shipping_terms(item.get("shipping_terms", ""))

        total_score = round(price_score + delivery_score + (term_score * 25.0 / 30.0) + (ship_score * 10.0 / 15.0), 1)

        item["score"] = total_score
        item["is_lowest_price"] = (amount == min_amount and amount > 0)
        item["is_fastest_delivery"] = (days == min_days and days > 0)
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
    comp_title = (buyer_company or {}).get("title", "KOBİ Satın Alma Direktörlüğü")
    comp_contact = (buyer_company or {}).get("contact_person", "Satın Alma Komisyonu")
    comp_phone = (buyer_company or {}).get("phone", "0850 300 40 50")
    comp_email = (buyer_company or {}).get("email", "satinalma@sirketiniz.com")

    tracking_code = quote.get("tracking_code", "TEKLIF-2026-0001")
    supplier_name = quote.get("supplier_name", "Tedarikçi Firma")
    amount = float(quote.get("total_amount", 0))
    currency = quote.get("currency", "TRY (₺)")
    terms = quote.get("payment_terms", "Vadeli")
    days = quote.get("delivery_days", 7)
    ref = quote.get("rfq_ref") or quote.get("rfq_category") or "Satın Alma İhalesi"

    subject = f"Sipariş Onayı ve Teklif Kabul Bildirimi (Ref: {tracking_code} / {ref})"

    body = f"""Sayın {supplier_name} Yetkilileri,

Şirketimize '{tracking_code}' takip referans numarası ile iletmiş olduğunuz '{ref}' konulu fiyat teklifiniz, Satın Alma Komisyonumuz tarafından incelenmiş ve en uygun teklif olarak KABUL EDİLMİŞTİR.

SİPARİŞ VE ANLAŞMA DETAYLARI:
--------------------------------------------------
Teklif / Sipariş Referansı : {tracking_code}
İlgili Talep / Şartname    : {ref}
Kabul Edilen Toplam Tutar  : {amount:,.2f} {currency} + KDV
Ödeme Vadesi ve Koşulları  : {terms}
Taahhüt Edilen Teslimat    : {days} İş Günü
Teslim Şekli               : {quote.get('shipping_terms', 'DDP')}
--------------------------------------------------

Sözleşme ve sipariş teyit yazımız hazırlanmış olup, kayıtlı KEP (Kayıtlı Elektronik Posta) adresinize resmi olarak tebliğ edilecektir. 

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
