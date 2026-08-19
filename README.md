# BDTE — Behavioral Digital Twin for Elderly

Capstone projesi monorepo iskeleti. Detaylı 15 haftalık plan için `docs/` klasörüne veya
paylaşılan `BDTE_Uygulama_Plani.docx` dosyasına bakın.

## Klasör yapısı

```
bdte/
├── backend/          # FastAPI (Python) — API, MCDM, RAG orkestrasyonu
│   └── app/
│       ├── main.py
│       ├── config.py
│       └── routers/  # health, profile, chat
├── frontend/         # React + Vite + TypeScript + Tailwind — sohbet arayüzü
├── ml-pipeline/       # MCDM (AHP/TOPSIS) ve veri işleme script'leri (Hafta 4+)
├── docs/              # Mimari diyagramlar, API sözleşmesi, toplantı notları
└── docker-compose.yml
```

## Gereksinimler

- Docker + Docker Compose
- (Opsiyonel ama önerilir) NVIDIA GPU + NVIDIA Container Toolkit — Ollama'nın hızlı çalışması için.
  GPU yoksa `docker-compose.yml`'de model olarak daha küçük bir model (ör. `qwen2.5:3b`) kullanın.

## Hızlı başlangıç

```bash
git clone <repo-url> bdte
cd bdte

# Tüm servisleri ayağa kaldır (db, ollama, backend, frontend)
docker compose up --build
```

İlk çalıştırmada Ollama modelini indirmeniz gerekir (konteyner ayaktayken, ayrı bir terminalde):

```bash
docker exec -it bdte-ollama ollama pull llama3.1:8b
# GPU yoksa / daha hafif bir model için:
# docker exec -it bdte-ollama ollama pull qwen2.5:3b
```

Servisler ayağa kalktığında:

| Servis | Adres |
|---|---|
| Frontend (sohbet arayüzü) | http://localhost:5173 |
| Backend API (Swagger docs) | http://localhost:8000/docs |
| PostgreSQL + pgvector | localhost:5432 (user: `bdte`, pass: `bdte`, db: `bdte`) |
| Ollama | http://localhost:11434 |

## Yerelde (Docker olmadan) geliştirme

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Git akışı

- `main`: her zaman çalışır durumda (demo edilebilir).
- Görev branch'leri: `feature/<kisa-aciklama>` (ör. `feature/mcdm-ahp`, `feature/tts-integration`).
- PR açmadan önce: `docker compose up --build` ile lokal test edin.
- En az 1 takım arkadaşı onayı ile merge edilir.

## Sıradaki adımlar (Hafta 1 sonrası)

- [ ] `backend/app/models.py` — SQLAlchemy tabloları (behavioral_profile, conversation_log, user)
- [ ] `ml-pipeline/ahp.py` — AHP pairwise comparison hesaplama scripti (Hafta 4)
- [ ] `backend/app/rag.py` — pgvector ile embedding arama + prompt oluşturma (Hafta 6)
- [ ] TTS servisi için ayrı bir `tts/` klasörü ve Coqui TTS entegrasyonu (Hafta 5)
