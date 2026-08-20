"""
BDTE — MCDM (Çok Kriterli Karar Verme) Modülü
================================================

NOT: Bu dosya backend/app/mcdm.py — uygulamanın "tek gerçek kaynağı" (single
source of truth). persona.py buradaki compute_ahp_weights() fonksiyonunu
doğrudan import edip çalışma anında (runtime) ağırlık hesaplar; ağırlıklar
elle iki yerde senkronize edilmez.

ml-pipeline/mcdm.py, bu dosyayı import edip aynı raporu bağımsız bir script
olarak da çalıştırabilmeniz için ince bir "runner" haline getirildi.

Bu script iki aşamalı MCDM sürecini uygular:

1. AHP (Analytic Hierarchy Process) — 5 davranışsal boyutun (duygusal
   örüntüler, iletişim tarzı, yaşam tercihleri, karar verme tarzı, ilişki
   dinamikleri) birbirine göre önemini, paydaşın (aile üyesinin) ikili
   karşılaştırmalarından hesaplar. Çıktı: her boyut için bir ağırlık
   (0-1 arası, toplamı 1) + tutarlılık oranı (CR — 0.10'un altında olmalı,
   yoksa karşılaştırmalar mantıksal olarak tutarsız demektir).

2. TOPSIS — Birden fazla alternatif persona/konfigürasyon tanımlandığında
   (örn. "daha resmi" vs "daha sıcak" vs "dengeli"), AHP ağırlıklarını
   kullanarak bunları puanlar ve en iyisini seçer.

NOT (rapor için önemli): Zaman kısıtı nedeniyle ikili karşılaştırma
değerleri gerçek bir aile üyesinden toplanan anket verisi yerine,
metodolojiyi doğrulamak amacıyla araştırmacı tarafından tanımlanmış
örnek/sentetik değerlerdir (bkz. backend/app/persona.py — EXAMPLE_PERSONA).
"""

import ahpy
import numpy as np
from pymcdm.methods import TOPSIS


# ---------------------------------------------------------------------------
# 1. AHP — Davranışsal boyutların ağırlıklarını hesapla
# ---------------------------------------------------------------------------

# İkili karşılaştırmalar: Saaty'nin 1-9 ölçeği kullanılır.
#   1 = eşit önemde, 3 = biraz daha önemli, 5 = kesinlikle daha önemli,
#   7 = çok güçlü derecede önemli, 9 = aşırı derecede önemli
#   (2, 4, 6, 8 = ara değerler)
# ('A', 'B'): x  →  A, B'den x kat daha önemlidir.
#
# Örnek senaryo: Bir aile üyesi (torun), anneannesini en çok "duygusal
# örüntüler" ve "iletişim tarzı" ile hatırladığını, "karar verme tarzı"nın
# ise diyalog deneyiminde daha az belirleyici olduğunu belirtiyor.
BEHAVIORAL_COMPARISONS = {
    ("emotional_patterns", "communication_style"): 2,
    ("emotional_patterns", "relationship_dynamics"): 2,
    ("emotional_patterns", "life_preferences"): 4,
    ("emotional_patterns", "decision_making_traits"): 5,
    ("communication_style", "relationship_dynamics"): 1,
    ("communication_style", "life_preferences"): 3,
    ("communication_style", "decision_making_traits"): 4,
    ("relationship_dynamics", "life_preferences"): 2,
    ("relationship_dynamics", "decision_making_traits"): 3,
    ("life_preferences", "decision_making_traits"): 2,
}


def compute_ahp_weights(comparisons: dict = BEHAVIORAL_COMPARISONS) -> dict:
    """
    AHP ile ikili karşılaştırmalardan ağırlık vektörünü ve tutarlılık
    oranını (CR) hesaplar.
    """
    compare = ahpy.Compare(name="behavioral_dimensions", comparisons=comparisons)
    weights = compare.target_weights  # {boyut: ağırlık} — toplamı 1.0
    cr = compare.consistency_ratio

    return {"weights": weights, "consistency_ratio": cr}


# ---------------------------------------------------------------------------
# 2. TOPSIS — Alternatif persona konfigürasyonlarını AHP ağırlıklarıyla sırala
# ---------------------------------------------------------------------------

# Her alternatif, 5 boyutta 1-10 arası bir "yoğunluk/belirginlik" puanına
# sahip olsun (örn. o alternatifte "duygusal örüntüler" ne kadar baskın
# işleniyor). Gerçek uygulamada bu puanlar da paydaş değerlendirmesinden
# gelir; burada örnek/sentetik olarak tanımlanmıştır.
ALTERNATIVE_CONFIGS = {
    "Sıcak ve Duygusal": {
        "emotional_patterns": 9, "communication_style": 8,
        "life_preferences": 6, "decision_making_traits": 4,
        "relationship_dynamics": 9,
    },
    "Dengeli": {
        "emotional_patterns": 7, "communication_style": 7,
        "life_preferences": 7, "decision_making_traits": 6,
        "relationship_dynamics": 7,
    },
    "Pratik ve Bilgilendirici": {
        "emotional_patterns": 4, "communication_style": 6,
        "life_preferences": 8, "decision_making_traits": 9,
        "relationship_dynamics": 5,
    },
}

DIMENSION_ORDER = [
    "emotional_patterns", "communication_style", "life_preferences",
    "decision_making_traits", "relationship_dynamics",
]


def compute_topsis_ranking(
    alternatives: dict = ALTERNATIVE_CONFIGS,
    weights: dict | None = None,
) -> list[tuple[str, float]]:
    """
    AHP'den gelen ağırlıkları kullanarak alternatif persona
    konfigürasyonlarını TOPSIS ile sıralar. Yüksek skor = ideal çözüme
    daha yakın (daha iyi alternatif).
    """
    if weights is None:
        weights = compute_ahp_weights()["weights"]

    alt_names = list(alternatives.keys())
    matrix = np.array([
        [alternatives[name][dim] for dim in DIMENSION_ORDER]
        for name in alt_names
    ], dtype=float)

    weight_vector = np.array([weights[dim] for dim in DIMENSION_ORDER])
    # Tüm boyutlar "fayda" (profit) kriteri — yüksek puan her zaman daha iyi.
    criteria_types = np.array([1] * len(DIMENSION_ORDER))  # 1 = profit, -1 = cost

    topsis = TOPSIS()
    scores = topsis(matrix, weight_vector, criteria_types)

    ranked = sorted(zip(alt_names, scores), key=lambda x: x[1], reverse=True)
    return ranked


# ---------------------------------------------------------------------------
# Çalıştırılabilir demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("1) AHP — Davranışsal Boyut Ağırlıkları")
    print("=" * 60)
    ahp_result = compute_ahp_weights()
    for dim, w in sorted(ahp_result["weights"].items(), key=lambda x: -x[1]):
        print(f"  {dim:28s} {w:.4f}")
    cr = ahp_result["consistency_ratio"]
    status = "✅ TUTARLI" if cr < 0.10 else "⚠️  TUTARSIZ (CR >= 0.10, karşılaştırmaları gözden geçir)"
    print(f"\n  Tutarlılık Oranı (CR): {cr:.4f}  →  {status}")

    print("\n" + "=" * 60)
    print("2) TOPSIS — Alternatif Persona Konfigürasyonu Sıralaması")
    print("=" * 60)
    ranking = compute_topsis_ranking(weights=ahp_result["weights"])
    for i, (name, score) in enumerate(ranking, start=1):
        print(f"  {i}. {name:28s} skor: {score:.4f}")

    print(f"\n  → Seçilen konfigürasyon: '{ranking[0][0]}'")
    print("    (persona.py'deki EXAMPLE_PERSONA bu ağırlıklarla hizalanmalı)")