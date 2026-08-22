# BDTE — Behavioral Digital Twin for Elderly

Yaşlı bireylerin (veya kaybedilmiş/uzaktaki sevdiklerin) davranışsal profilini, **AHP
(Analytic Hierarchy Process)** ile kişiye özel ağırlıklandırarak bir sohbet karakterine
(persona) dönüştüren, sesli ve avatarlı bir diyalog sistemi.

> **Not:** Zaman kısıtı nedeniyle proje, gerçek katılımcı verisi yerine kullanıcı
> tarafından tanımlanan sentetik/örnek personalarla çalışır. Metodoloji (AHP+TOPSIS,
> prompt engineering ile davranışsal temellendirme) gerçek veriyle aynı şekilde işler —
> bkz. [Sınırlamalar](#bilinen-sınırlamalar--gelecek-çalışma).

## Mimari

```
Tarayıcı (React, :5173)
      │  fetch (JSON)
      ▼
Backend — FastAPI (:8000)
      │
      ├─ SQLite (bdte.db) ─── persona'lar + konuşma geçmişi
      ├─ Ollama (:11434) ──── LLM (Llama 3.1 8B) — persona bazlı diyalog
      └─ Coqui TTS (XTTS-v2) ─ cinsiyete uyarlanmış sesli yanıt
```

Her persona'nın 5 davranışsal boyutu (duygusal örüntüler, iletişim tarzı, yaşam
tercihleri, karar verme tarzı, ilişki dinamikleri) vardır. Kullanıcı bu 5 boyut
arasında 10 ikili karşılaştırma yapar (Saaty ölçeği); backend bunlardan **AHP ile o
persona'ya özel ağırlıkları** hesaplar. Bu ağırlıklar, LLM'e verilen system prompt'ta
boyutların önem sırasını belirler.

## Klasör yapısı

```
bdte/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI giriş noktası, seed persona
│       ├── config.py        # ortam değişkenleri
│       ├── database.py      # SQLAlchemy (SQLite) bağlantısı
│       ├── models.py        # BehavioralProfile, ConversationMessage tabloları
│       ├── mcdm.py          # AHP (ağırlık hesabı) + TOPSIS
│       ├── persona.py       # system prompt üretimi, seed persona verisi
│       ├── tts.py           # Coqui TTS (XTTS-v2) entegrasyonu
│       └── routers/
│           ├── health.py
│           ├── profile.py   # persona CRUD (liste/detay/oluştur/düzenle/sil)
│           ├── chat.py      # diyalog endpoint'i
│           └── tts.py       # metin→ses endpoint'i
├── frontend/
│   └── src/
│       ├── App.tsx                    # ana sohbet arayüzü
│       └── components/
│           ├── Avatar.tsx             # cinsiyet/yaşa uyarlanmış SVG avatar
│           └── PersonaForm.tsx        # persona oluşturma/düzenleme formu (AHP kaydırıcıları)
└── ml-pipeline/
    └── mcdm.py               # backend/app/mcdm.py'yi kullanan bağımsız rapor scripti
```

## Gereksinimler

- Python 3.11+ ([uv](https://docs.astral.sh/uv/) ile kurulum önerilir)
- Node.js 20+
- [Ollama](https://ollama.com) (yerel LLM çalıştırmak için)
- (Önerilir) NVIDIA GPU — TTS ve LLM gecikmesini ciddi şekilde azaltır. GPU yoksa
  `backend/app/config.py`'de daha küçük bir Ollama modeli (ör. `qwen2.5:3b`) kullanılabilir.

## Kurulum

### 1) Ollama ve model

```bash
# ollama.com/download üzerinden kur, sonra:
ollama pull llama3.1:8b
```

### 2) Backend

```bash
cd backend
uv venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
uv pip install -r requirements.txt
uvicorn app.main:app --reload
```

İlk çalıştırmada:
- `bdte.db` (SQLite) otomatik oluşturulur
- Örnek bir persona ("Nezahat Yılmaz") otomatik eklenir (seed)
- TTS modelini ilk kullanımda (`/api/tts/` ilk çağrıldığında) Coqui otomatik indirir (~2GB,
  Coqui Public Model License / CPML onayı ister — bkz. https://coqui.ai/cpml.txt)

### 3) Frontend

```bash
cd frontend
npm install
npm run dev
```

Servisler ayağa kalktığında:

| Servis | Adres |
|---|---|
| Frontend (sohbet arayüzü) | http://localhost:5173 |
| Backend API (Swagger docs) | http://localhost:8000/docs |
| Ollama | http://localhost:11434 |

## API özeti

| Endpoint | Açıklama |
|---|---|
| `GET /api/profile/` | Tüm persona'ları listeler |
| `GET /api/profile/{id}` | Bir persona'nın tüm detayını (boyutlar, ağırlıklar, ham karşılaştırmalar) döner |
| `POST /api/profile/` | Yeni persona oluşturur (5 boyut + 10 ikili karşılaştırma → AHP ağırlıkları hesaplanır) |
| `PUT /api/profile/{id}` | Var olan bir persona'yı düzenler, ağırlıkları yeniden hesaplar |
| `DELETE /api/profile/{id}` | Persona'yı ve ona ait sohbet geçmişini siler (son persona silinemez) |
| `POST /api/chat/` | Seçili persona ile sohbet eder, geçmişi SQLite'a kalıcı yazar |
| `POST /api/tts/` | Metni sese çevirir (persona'nın cinsiyetine göre ses seçilir) |

Tam ve interaktif dokümantasyon için backend çalışırken `http://localhost:8000/docs`
adresine bakılabilir (FastAPI/Swagger otomatik üretir).

## MCDM raporunu bağımsız çalıştırma

```bash
cd ml-pipeline
python mcdm.py
```

AHP ağırlıklarını, tutarlılık oranını (CR) ve TOPSIS sıralamasını terminalde gösterir
(backend'i ayağa kaldırmadan, sadece yöntemi doğrulamak için).

## Bilinen sınırlamalar / gelecek çalışma

- **Sentetik veri:** Gerçek katılımcı görüşmesi/anketi yerine, kullanıcı tarafından
  tanımlanan örnek personalar kullanılıyor (zaman kısıtı). AHP/TOPSIS metodolojisi
  gerçek veriyle aynı şekilde çalışır.
- **SQLite (PostgreSQL+pgvector değil):** Şu an gerçek embedding tabanlı RAG (uzun
  vadeli hafıza) yok; persona, prompt engineering ile "system prompt" olarak
  enjekte ediliyor. İleride pgvector'a geçiş, `DATABASE_URL`'i değiştirmekten
  ibaret olacak şekilde tasarlandı.
- **TTS gecikmesi:** ~3 saniye (GPU ısınması sonrası), streaming olmayan üretim
  nedeniyle. Orijinal hedeflenen <1000ms'nin üzerinde.
- **Avatar:** Gerçek lip-sync değil, basit ağız açma/kapama animasyonu (ağır
  GPU gerektiren SadTalker/Wav2Lip gibi modeller MVP kapsamı dışı bırakıldı).
- **Guardrail:** Hassas konularda (sağlık, ölüm, yalnızlık) şu an yalnızca prompt
  seviyesinde bir yönlendirme var; ayrı bir güvenlik katmanı yok.