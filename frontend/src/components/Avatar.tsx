import { useEffect, useState } from "react";

interface AvatarProps {
  isSpeaking: boolean;
  gender?: "female" | "male";
  age?: number | null;
}

/**
 * A simple, code-drawn SVG avatar. Hair style/color, glasses (60+ years),
 * and clothing color adapt to gender and age. Does not do real lip-sync —
 * while audio plays, the mouth toggles open/closed quickly to give a
 * "speaking" impression, plus a soft glow ring.
 * WP4 MVP scope: heavy GPU-based real lip-sync models (SadTalker/Wav2Lip)
 * were deliberately left out of scope.
 */
export default function Avatar({ isSpeaking, gender = "female", age = null }: AvatarProps) {
  const [mouthOpen, setMouthOpen] = useState(false);

  useEffect(() => {
    if (!isSpeaking) {
      setMouthOpen(false);
      return;
    }
    const interval = setInterval(() => setMouthOpen((prev) => !prev), 180);
    return () => clearInterval(interval);
  }, [isSpeaking]);

  const isElderly = (age ?? 65) >= 60; // default to elderly look if age is unknown
  const isFemale = gender === "female";

  // Hair color: gray/white if elderly, otherwise a dark tone based on gender.
  const hairColor = isElderly ? "#D9D9D9" : isFemale ? "#4A3728" : "#2E2E2E";
  // Clothing color: purple for female, blue-gray for male.
  const clothingColor = isFemale ? "#8B6F9E" : "#4A6FA5";

  return (
    <div className="relative flex items-center justify-center">
      <div
        className={`absolute w-36 h-36 rounded-full bg-amber-200 transition-opacity duration-300 ${
          isSpeaking ? "opacity-60 animate-pulse" : "opacity-0"
        }`}
      />

      <svg width="120" height="120" viewBox="0 0 120 120" className="relative drop-shadow-md">
        {/* Head */}
        <circle cx="60" cy="58" r="34" fill="#E8B894" />

        {/* Hair — female: bun, male: short/side-parted */}
        {isFemale ? (
          <>
            <path d="M28 55 Q26 22 60 20 Q94 22 92 55 Q92 40 60 36 Q28 40 28 55 Z" fill={hairColor} />
            <circle cx="60" cy="22" r="10" fill={hairColor} />
          </>
        ) : (
          <path d="M27 52 Q26 24 60 22 Q94 24 93 52 Q90 32 60 30 Q30 32 27 52 Z" fill={hairColor} />
        )}

        {/* Ears */}
        <circle cx="27" cy="60" r="5" fill="#E8B894" />
        <circle cx="93" cy="60" r="5" fill="#E8B894" />

        {/* Glasses — only for 60+ */}
        {isElderly && (
          <>
            <circle cx="46" cy="55" r="10" fill="none" stroke="#6B7280" strokeWidth="2.5" />
            <circle cx="74" cy="55" r="10" fill="none" stroke="#6B7280" strokeWidth="2.5" />
            <line x1="56" y1="55" x2="64" y2="55" stroke="#6B7280" strokeWidth="2.5" />
          </>
        )}

        {/* Eyes */}
        <circle cx="46" cy="55" r="2.5" fill="#3F2E1E" />
        <circle cx="74" cy="55" r="2.5" fill="#3F2E1E" />

        {/* Cheeks */}
        <circle cx="38" cy="70" r="6" fill="#F3A6A6" opacity="0.5" />
        <circle cx="82" cy="70" r="6" fill="#F3A6A6" opacity="0.5" />

        {/* Mouth — toggles open/closed while speaking */}
        {mouthOpen ? (
          <ellipse cx="60" cy="78" rx="8" ry="6" fill="#7A3B3B" />
        ) : (
          <path d="M50 78 Q60 84 70 78" fill="none" stroke="#7A3B3B" strokeWidth="3" strokeLinecap="round" />
        )}

        {/* Neck and shoulders */}
        <rect x="50" y="88" width="20" height="10" fill="#E8B894" />
        <path d="M20 120 Q60 95 100 120 Z" fill={clothingColor} />
      </svg>
    </div>
  );
}
