"""
Veritabanı bağlantısı (SQLite — yerel geliştirme için).

NOT (zaman kısıtı kararı): Orijinal planda PostgreSQL + pgvector vardı,
gerçek RAG (embedding tabanlı arama) için. Şu an persona sabit bir
"system prompt" olarak enjekte ediliyor (embedding araması yok), bu
yüzden SQLite yeterli ve native Windows'ta sıfır ek kurulum gerektiriyor.

İleride gerçek RAG'e geçilirse: DATABASE_URL'i bir PostgreSQL+pgvector
adresine çevirmek yeterli — SQLAlchemy modelleri (models.py) değişmeden
çalışmaya devam eder.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

# SQLite için "check_same_thread=False" gerekli çünkü FastAPI istekleri
# farklı thread'lerde işleyebilir.
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — her istekte bir DB session açar, sonunda kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Tabloları (henüz yoksa) oluşturur. Uygulama başlarken bir kez çağrılır."""
    Base.metadata.create_all(bind=engine)