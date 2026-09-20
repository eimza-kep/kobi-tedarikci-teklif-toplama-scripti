@echo off
chcp 65001 >nul
echo =================================================================
echo        KOBİ TEDARİKÇİ TEKLİF TOPLAMA SİSTEMİ BAŞLATICI
echo =================================================================
echo.
echo Sunucu hazırlanıyor ve başlatılıyor...
echo Port: 8090
echo.
start "" http://localhost:8090
python server.py
pause
