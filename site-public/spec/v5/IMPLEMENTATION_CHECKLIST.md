# Implementation Checklist
Date: 2026-03-24

## Laptop Sonrası - Öncelik Sırası

1. Parent-link implementasyonu
   → Her seal öncekini referanslar
   → Zincir koparsa görünür

2. Append-only manifest
   → Her seal otomatik eklenir
   → Silinemez, sadece eklenir
   → "Seal vardı ama dosyası yok" tespit edilir
   → Parent-link ile birlikte implement edilmeli

3. Linked chain doğrulama
   → Zincir bütünlüğü kontrol

4. V5 temiz implementasyon

5. Agent proof hattı düzenleme

6. Canonical spec v4 (tek sayfa)

7. How to verify (5 adım)

8. Whitepaper

## Not

Append-only manifest + parent-link birbirini tamamlar.
İkisi ayrı implement edilirse eksik kalır.
