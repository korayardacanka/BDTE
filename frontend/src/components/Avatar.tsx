import { useEffect, useState } from "react";

interface AvatarProps {
  isSpeaking: boolean;
}

/**
 * Basit, kod ile çizilmiş SVG avatar (Nezahat Yılmaz persona'sı için).
 * Gerçek lip-sync yapmıyor — ses çalarken ağız açık/kapalı arasında hızlıca
 * geçiş yaparak "konuşuyor" hissi veriyor, artı hafif bir parıltı halkası.
 * WP4'ün MVP kapsamı: ağır GPU gerektiren gerçek lip-sync modelleri
 * (SadTalker/Wav2Lip) bilinçli olarak kapsam dışı bırakıldı.
 */
export default function Avatar({ isSpeaking }: AvatarProps) {
  const [mouthOpen, setMouthOpen] = useState(false);

  useEffect(() => {
    if (!isSpeaking) {
      setMouthOpen(false);
      return;
    }
    const interval = setInterval(() => {
      setMouthOpen((prev) => !prev);
    }, 180);
    return () => clearInterval(interval);
  }, [isSpeaking]);

  return (
    <div className="relative flex items-center justify-center">
      {/* Konuşurken beliren parıltı halkası */}
      <div
        className={`absolute w-36 h-36 rounded-full bg-amber-200 transition-opacity duration-300 ${
          isSpeaking ? "opacity-60 animate-pulse" : "opacity-0"
        }`}
      />

      <svg
        width="120"
        height="120"
        viewBox="0 0 120 120"
        className="relative drop-shadow-md"
      >
        {/* Baş */}
        <circle cx="60" cy="58" r="34" fill="#E8B894" />

        {/* Saç (topuz) */}
        <path
          d="M28 55 Q26 22 60 20 Q94 22 92 55 Q92 40 60 36 Q28 40 28 55 Z"
          fill="#D9D9D9"
        />
        <circle cx="60" cy="22" r="10" fill="#D9D9D9" />

        {/* Kulaklar */}
        <circle cx="27" cy="60" r="5" fill="#E8B894" />
        <circle cx="93" cy="60" r="5" fill="#E8B894" />

        {/* Gözlük */}
        <circle cx="46" cy="55" r="10" fill="none" stroke="#6B7280" strokeWidth="2.5" />
        <circle cx="74" cy="55" r="10" fill="none" stroke="#6B7280" strokeWidth="2.5" />
        <line x1="56" y1="55" x2="64" y2="55" stroke="#6B7280" strokeWidth="2.5" />

        {/* Gözler */}
        <circle cx="46" cy="55" r="2.5" fill="#3F2E1E" />
        <circle cx="74" cy="55" r="2.5" fill="#3F2E1E" />

        {/* Yanaklar */}
        <circle cx="38" cy="70" r="6" fill="#F3A6A6" opacity="0.5" />
        <circle cx="82" cy="70" r="6" fill="#F3A6A6" opacity="0.5" />

        {/* Ağız — konuşurken açık/kapalı arasında geçiş yapar */}
        {mouthOpen ? (
          <ellipse cx="60" cy="78" rx="8" ry="6" fill="#7A3B3B" />
        ) : (
          <path
            d="M50 78 Q60 84 70 78"
            fill="none"
            stroke="#7A3B3B"
            strokeWidth="3"
            strokeLinecap="round"
          />
        )}

        {/* Boyun ve omuzlar (basit) */}
        <rect x="50" y="88" width="20" height="10" fill="#E8B894" />
        <path d="M20 120 Q60 95 100 120 Z" fill="#8B6F9E" />
      </svg>
    </div>
  );
}