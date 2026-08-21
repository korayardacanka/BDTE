"""
TTS (Text-to-Speech) modülü — Coqui TTS (XTTS-v2) ile sesli yanıt üretimi.

NOT: "coqui-tts" paketi kullanılıyor (idiap fork) — orijinal "TTS" paketi
artık bakımsız (Coqui AI şirketi 2024'te kapandı, orijinal paket Python
<3.11 ile sınırlı kaldı). Bu proje Python 3.11 kullandığı için ikisi de
teknik olarak çalışabilir, ama güncel/bakımlı olan fork tercih edildi.

XTTS-v2 modeli Coqui Public Model License (CPML) altındadır — akademik/
ticari olmayan kullanım için uygundur (bkz. https://coqui.ai/cpml.txt).
Bu, capstone projesi kapsamında (ticari olmayan) sorunsuz kullanılabilir,
ama raporda lisans notunun belirtilmesi iyi olur.

Model ilk çağrıldığında Hugging Face'ten indirilir (~2GB) — bu işlem
birkaç dakika sürebilir ve internet bağlantısı gerektirir. Sonraki
çağrılar çok daha hızlıdır çünkü model bellekte/diskte kalır.
"""
import threading

_tts_instance = None
_lock = threading.Lock()

# Modelin önceden tanımlı (built-in) konuşmacılarından, cinsiyete göre biri
# seçilir — herhangi bir ses örneği (speaker_wav) kaydetmeye gerek kalmadan.
# TODO (gelecek çalışma): persona'nın yaşına/sesine daha da uygun bir
# referans ses klonlama (speaker_wav) ile kişiselleştirme derinleştirilebilir.
GENDER_SPEAKER_MAP = {
    "kadın": "Ana Florence",
    "erkek": "Craig Gutsy",
}
DEFAULT_SPEAKER = GENDER_SPEAKER_MAP["kadın"]


def _get_tts():
    """
    TTS modelini yalnızca bir kez (ilk çağrıda) yükler ve bellekte tutar
    (lazy singleton). Model yüklemesi ağır olduğu için her istekte yeniden
    yüklenmesini istemiyoruz.
    """
    global _tts_instance
    if _tts_instance is None:
        with _lock:
            if _tts_instance is None:  # double-checked locking
                import torch
                from TTS.api import TTS

                gpu = torch.cuda.is_available()
                _tts_instance = TTS(
                    "tts_models/multilingual/multi-dataset/xtts_v2", gpu=gpu
                )
    return _tts_instance


def synthesize_speech(
    text: str, output_path: str, language: str = "tr", gender: str | None = None
) -> str:
    """
    Metni sese çevirir, wav dosyasına yazar, dosya yolunu döner.
    gender belirtilmişse ("kadın"/"erkek"), o cinsiyete uygun ses kullanılır.
    """
    tts = _get_tts()
    speaker = GENDER_SPEAKER_MAP.get(gender, DEFAULT_SPEAKER)
    tts.tts_to_file(
        text=text,
        speaker=speaker,
        language=language,
        file_path=output_path,
    )
    return output_path