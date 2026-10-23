# -*- coding: utf-8 -*-
"""
scripts/rfq_order_xml_generator.py
-----------------------------------
GİB UBL-TR 2.1 Standardında Elektronik Satın Alma Sipariş Fişi (Order XML) Üretici Motoru.
KOBİ'lerin onaylanan teklifleri muhasebe/ERP sistemlerine (e-Fatura / e-Sipariş entegratörleri)
GİB standart UBL-TR 2.1 XML olarak aktarmasını sağlar.
"""

import uuid
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
    "kep_address": "kobisirket@hs01.kep.tr"
}

def clean_currency_code(curr_str):
    """Para birimi kodunu 3 haneli ISO formatına (TRY, USD, EUR) dönüştürür."""
    if not curr_str:
        return "TRY"
    curr = str(curr_str).upper()
    if "USD" in curr or "$" in curr:
        return "USD"
    if "EUR" in curr or "€" in curr:
        return "EUR"
    return "TRY"

def parse_items(quote, items_override=None):
    """
    Tekliften veya parametreden sipariş kalemlerini ayrıştırır.
    Eğer çoklu kalem belirtilmemişse genel teklif bilgisinden tek bir sipariş kalemi üretir.
    """
    if items_override and isinstance(items_override, list) and len(items_override) > 0:
        return items_override

    gross_amount = float(quote.get("total_amount", 0.0))
    discount_amount = float(quote.get("discount_amount", 0.0))
    net_amount = max(0.0, gross_amount - discount_amount)

    cat = quote.get("rfq_category") or "Satın Alma Siparişi"
    details = quote.get("quote_details") or f"{cat} - {quote.get('rfq_ref', 'Talep')}"

    return [
        {
            "line_id": 1,
            "name": cat,
            "description": details,
            "quantity": 1.0,
            "unit_code": "C62", # C62 = Adet / Unit
            "unit_price": gross_amount,
            "discount_amount": discount_amount,
            "line_total": net_amount
        }
    ]

def generate_ubl_order_xml(quote, buyer_company=None, items=None, order_id=None):
    """
    GİB UBL-TR 2.1 Satın Alma Siparişi (Order XML) üretir.
    
    Standart Yapı:
    - Root: <Order xmlns="urn:oasis:names:specification:ubl:schema:xsd:Order-2" ...>
    - UBLVersionID: 2.1
    - CustomizationID: TR1.2
    - ProfileID: TICARISIPARIS
    - Party bilgileri (Alıcı / Satıcı)
    - Vergi ve İskonto toplamları
    - Sipariş Kalemleri (OrderLine)
    """
    buyer = buyer_company or DEFAULT_BUYER
    currency = clean_currency_code(quote.get("currency", "TRY"))
    
    tracking_code = quote.get("tracking_code", "TEKLIF-2026-0001")
    generated_order_id = order_id or f"SIP-{datetime.date.today().strftime('%Y%m%d')}-{tracking_code.replace('TEKLIF-', '')[-4:]}"
    order_uuid = str(uuid.uuid4())
    issue_date = datetime.date.today().strftime("%Y-%m-%d")
    issue_time = datetime.datetime.now().strftime("%H:%M:%S")

    order_items = parse_items(quote, items)
    
    # Kalem toplamlarını hesapla
    subtotal_raw = sum(float(item.get("unit_price", 0.0)) * float(item.get("quantity", 1.0)) for item in order_items)
    total_discount = sum(float(item.get("discount_amount", 0.0)) for item in order_items)
    if total_discount == 0 and float(quote.get("discount_amount", 0.0)) > 0:
        total_discount = float(quote.get("discount_amount", 0.0))

    line_extension_amount = max(0.0, subtotal_raw - total_discount)
    vat_rate = float(quote.get("vat_rate", 20.0))
    vat_amount = round(line_extension_amount * (vat_rate / 100.0), 2)
    payable_amount = round(line_extension_amount + vat_amount, 2)

    supplier_vkn = str(quote.get("supplier_vkn", "1111111111")).strip()
    buyer_vkn = str(buyer.get("vkn", "5810492810")).strip()
    supplier_name = quote.get("supplier_name", "Tedarikçi Firma")
    payment_terms = quote.get("payment_terms", "30 Gün Vadeli")
    shipping_terms = quote.get("shipping_terms", "DDP Adrese Teslim")
    delivery_days = quote.get("delivery_days", 7)
    note_text = f"Sipariş Referansı: {tracking_code}. Talep No: {quote.get('rfq_ref', '-')}. Teslimat Süresi: {delivery_days} İş Günü. Nakliye: {shipping_terms}."

    # XML String Üretimi
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Order xmlns="urn:oasis:names:specification:ubl:schema:xsd:Order-2"',
        '       xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"',
        '       xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">',
        '  <cbc:UBLVersionID>2.1</cbc:UBLVersionID>',
        '  <cbc:CustomizationID>TR1.2</cbc:CustomizationID>',
        '  <cbc:ProfileID>TICARISIPARIS</cbc:ProfileID>',
        f'  <cbc:ID>{escape(generated_order_id)}</cbc:ID>',
        '  <cbc:CopyIndicator>false</cbc:CopyIndicator>',
        f'  <cbc:UUID>{order_uuid}</cbc:UUID>',
        f'  <cbc:IssueDate>{issue_date}</cbc:IssueDate>',
        f'  <cbc:IssueTime>{issue_time}</cbc:IssueTime>',
        '  <cbc:OrderTypeCode>SATINALMA</cbc:OrderTypeCode>',
        f'  <cbc:Note>{escape(note_text)}</cbc:Note>',
        f'  <cbc:DocumentCurrencyCode>{currency}</cbc:DocumentCurrencyCode>',
        '  <cac:BuyerCustomerParty>',
        '    <cac:Party>',
        '      <cac:PartyIdentification>',
        f'        <cbc:ID schemeID="VKN">{escape(buyer_vkn)}</cbc:ID>',
        '      </cac:PartyIdentification>',
        '      <cac:PartyName>',
        f'        <cbc:Name>{escape(buyer.get("title", "Alıcı Firma"))}</cbc:Name>',
        '      </cac:PartyName>',
        '      <cac:PostalAddress>',
        f'        <cbc:StreetName>{escape(buyer.get("address", "Adres Bilgisi"))}</cbc:StreetName>',
        f'        <cbc:CityName>{escape(buyer.get("city", "İstanbul"))}</cbc:CityName>',
        '        <cac:Country>',
        '          <cbc:Name>Türkiye</cbc:Name>',
        '        </cac:Country>',
        '      </cac:PostalAddress>',
        '      <cac:PartyTaxScheme>',
        '        <cac:TaxScheme>',
        f'          <cbc:Name>{escape(buyer.get("tax_office", "Vergi Dairesi"))}</cbc:Name>',
        '        </cac:TaxScheme>',
        '      </cac:PartyTaxScheme>',
        '      <cac:Contact>',
        f'        <cbc:Telephone>{escape(buyer.get("phone", ""))}</cbc:Telephone>',
        f'        <cbc:ElectronicMail>{escape(buyer.get("email", ""))}</cbc:ElectronicMail>',
        '      </cac:Contact>',
        '    </cac:Party>',
        '  </cac:BuyerCustomerParty>',
        '  <cac:SellerSupplierParty>',
        '    <cac:Party>',
        '      <cac:PartyIdentification>',
        f'        <cbc:ID schemeID="{"VKN" if len(supplier_vkn)==10 else "TCKN"}">{escape(supplier_vkn)}</cbc:ID>',
        '      </cac:PartyIdentification>',
        '      <cac:PartyName>',
        f'        <cbc:Name>{escape(supplier_name)}</cbc:Name>',
        '      </cac:PartyName>',
        '      <cac:PostalAddress>',
        f'        <cbc:StreetName>{escape(quote.get("supplier_city", "Türkiye"))}</cbc:StreetName>',
        f'        <cbc:CityName>{escape(quote.get("supplier_city", "Türkiye"))}</cbc:CityName>',
        '        <cac:Country>',
        '          <cbc:Name>Türkiye</cbc:Name>',
        '        </cac:Country>',
        '      </cac:PostalAddress>',
        '      <cac:Contact>',
        f'        <cbc:Telephone>{escape(quote.get("supplier_phone", ""))}</cbc:Telephone>',
        f'        <cbc:ElectronicMail>{escape(quote.get("supplier_email", ""))}</cbc:ElectronicMail>',
        '      </cac:Contact>',
        '    </cac:Party>',
        '  </cac:SellerSupplierParty>',
        '  <cac:Delivery>',
        '    <cac:DeliveryTerms>',
        f'      <cbc:ID>{escape(shipping_terms[:10])}</cbc:ID>',
        f'      <cbc:SpecialTerms>{escape(shipping_terms)}</cbc:SpecialTerms>',
        '    </cac:DeliveryTerms>',
        '    <cac:RequestedDeliveryPeriod>',
        f'      <cbc:Description>{delivery_days} İş Günü</cbc:Description>',
        '    </cac:RequestedDeliveryPeriod>',
        '  </cac:Delivery>',
        '  <cac:PaymentTerms>',
        f'    <cbc:Note>{escape(payment_terms)}</cbc:Note>',
        '  </cac:PaymentTerms>'
    ]

    # İskonto varsa AllowanceCharge ekle
    if total_discount > 0:
        xml_lines.extend([
            '  <cac:AllowanceCharge>',
            '    <cbc:ChargeIndicator>false</cbc:ChargeIndicator>',
            '    <cbc:AllowanceChargeReason>Satın Alma İskontosu</cbc:AllowanceChargeReason>',
            f'    <cbc:Amount currencyID="{currency}">{total_discount:.2f}</cbc:Amount>',
            '  </cac:AllowanceCharge>'
        ])

    # KDV Toplamı
    xml_lines.extend([
        '  <cac:TaxTotal>',
        f'    <cbc:TaxAmount currencyID="{currency}">{vat_amount:.2f}</cbc:TaxAmount>',
        '    <cac:TaxSubtotal>',
        f'      <cbc:TaxableAmount currencyID="{currency}">{line_extension_amount:.2f}</cbc:TaxableAmount>',
        f'      <cbc:TaxAmount currencyID="{currency}">{vat_amount:.2f}</cbc:TaxAmount>',
        f'      <cbc:Percent>{vat_rate:.0f}</cbc:Percent>',
        '      <cac:TaxCategory>',
        '        <cac:TaxScheme>',
        '          <cbc:Name>KDV</cbc:Name>',
        '          <cbc:TaxTypeCode>0015</cbc:TaxTypeCode>',
        '        </cac:TaxScheme>',
        '      </cac:TaxCategory>',
        '    </cac:TaxSubtotal>',
        '  </cac:TaxTotal>',
        '  <cac:AnticipatedMonetaryTotal>',
        f'    <cbc:LineExtensionAmount currencyID="{currency}">{line_extension_amount:.2f}</cbc:LineExtensionAmount>',
        f'    <cbc:TaxExclusiveAmount currencyID="{currency}">{line_extension_amount:.2f}</cbc:TaxExclusiveAmount>',
        f'    <cbc:TaxInclusiveAmount currencyID="{currency}">{payable_amount:.2f}</cbc:TaxInclusiveAmount>',
        f'    <cbc:AllowanceTotalAmount currencyID="{currency}">{total_discount:.2f}</cbc:AllowanceTotalAmount>',
        f'    <cbc:PayableAmount currencyID="{currency}">{payable_amount:.2f}</cbc:PayableAmount>',
        '  </cac:AnticipatedMonetaryTotal>'
    ])

    # Sipariş Kalemleri
    for idx, item in enumerate(order_items, start=1):
        line_id = item.get("line_id", idx)
        q_val = float(item.get("quantity", 1.0))
        u_code = item.get("unit_code", "C62")
        u_price = float(item.get("unit_price", 0.0))
        l_disc = float(item.get("discount_amount", 0.0))
        l_ext = (u_price * q_val) - l_disc
        i_name = item.get("name", f"Kalem {line_id}")
        i_desc = item.get("description", i_name)

        xml_lines.extend([
            '  <cac:OrderLine>',
            f'    <cbc:ID>{line_id}</cbc:ID>',
            '    <cac:LineItem>',
            f'      <cbc:ID>{line_id}</cbc:ID>',
            f'      <cbc:Quantity unitCode="{u_code}">{q_val:.2f}</cbc:Quantity>',
            f'      <cbc:LineExtensionAmount currencyID="{currency}">{l_ext:.2f}</cbc:LineExtensionAmount>',
            '      <cac:Price>',
            f'        <cbc:PriceAmount currencyID="{currency}">{u_price:.2f}</cbc:PriceAmount>',
            '      </cac:Price>',
            '      <cac:Item>',
            f'        <cbc:Description>{escape(i_desc)}</cbc:Description>',
            f'        <cbc:Name>{escape(i_name)}</cbc:Name>',
            '      </cac:Item>',
            '    </cac:LineItem>',
            '  </cac:OrderLine>'
        ])

    xml_lines.append('</Order>\n')
    return "\n".join(xml_lines)
