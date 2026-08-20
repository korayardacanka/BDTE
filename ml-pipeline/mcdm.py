"""
BDTE — MCDM Rapor Çalıştırıcısı (Runner)
==========================================

Asıl AHP/TOPSIS mantığı backend/app/mcdm.py'de yaşıyor (tek gerçek kaynak —
persona.py da ağırlıkları buradan çalışma anında çekiyor). Bu script,
backend'i ayağa kaldırmadan, sadece MCDM raporunu terminalde görmek
isteyenler için ince bir çalıştırıcıdır.

Çalıştırmak için backend'in sanal ortamının aktif olması gerekir
(ahpy, pymcdm, numpy kurulu olmalı):

    cd backend && .venv\\Scripts\\activate   (Windows)
    cd ../ml-pipeline
    python mcdm.py
"""
import os
import sys

# backend/ klasörünü Python path'ine ekle, böylece "app.mcdm" import edilebilsin.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.mcdm import compute_ahp_weights, compute_topsis_ranking  # noqa: E402

if __name__ == "__main__":
    print("=" * 60)
    print("1) AHP — Davranışsal Boyut Ağırlıkları")
    print("=" * 60)
    ahp_result = compute_ahp_weights()
    for dim, w in sorted(ahp_result["weights"].items(), key=lambda x: -x[1]):
        print(f"  {dim:28s} {w:.4f}")
    cr = ahp_result["consistency_ratio"]
    status = "✅ TUTARLI" if cr < 0.10 else "⚠️  TUTARSIZ (CR >= 0.10)"
    print(f"\n  Tutarlılık Oranı (CR): {cr:.4f}  →  {status}")

    print("\n" + "=" * 60)
    print("2) TOPSIS — Alternatif Persona Konfigürasyonu Sıralaması")
    print("=" * 60)
    ranking = compute_topsis_ranking(weights=ahp_result["weights"])
    for i, (name, score) in enumerate(ranking, start=1):
        print(f"  {i}. {name:28s} skor: {score:.4f}")

    print(f"\n  → Seçilen konfigürasyon: '{ranking[0][0]}'")
    print("    (persona.py bu ağırlıkları artık OTOMATİK olarak kullanıyor)")