import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// NOT: Bu etiketler ve sıralama backend/app/persona.py'deki
// DIMENSION_LABELS / COMPARISON_PAIRS ile birebir eşleşmeli.
const DIMENSION_LABELS: Record<string, string> = {
  emotional_patterns: "Duygusal örüntüler",
  communication_style: "İletişim tarzı",
  life_preferences: "Yaşam tercihleri",
  decision_making_traits: "Karar verme tarzı",
  relationship_dynamics: "İlişki dinamikleri",
};

const DIMENSION_KEYS = Object.keys(DIMENSION_LABELS);

const COMPARISON_PAIRS: [string, string][] = [
  ["emotional_patterns", "communication_style"],
  ["emotional_patterns", "relationship_dynamics"],
  ["emotional_patterns", "life_preferences"],
  ["emotional_patterns", "decision_making_traits"],
  ["communication_style", "relationship_dynamics"],
  ["communication_style", "life_preferences"],
  ["communication_style", "decision_making_traits"],
  ["relationship_dynamics", "life_preferences"],
  ["relationship_dynamics", "decision_making_traits"],
  ["life_preferences", "decision_making_traits"],
];

// Saaty ölçeği — 9 kademeli, simetrik (sol taraf A lehine, sağ taraf B lehine)
const SCALE_STEPS = [
  { value: 9, more_important: "a" as const, label: "çok daha önemli" },
  { value: 7, more_important: "a" as const, label: "önemli ölçüde daha önemli" },
  { value: 5, more_important: "a" as const, label: "biraz daha önemli" },
  { value: 3, more_important: "a" as const, label: "hafifçe daha önemli" },
  { value: 1, more_important: "a" as const, label: "eşit önemde" },
  { value: 3, more_important: "b" as const, label: "hafifçe daha önemli" },
  { value: 5, more_important: "b" as const, label: "biraz daha önemli" },
  { value: 7, more_important: "b" as const, label: "önemli ölçüde daha önemli" },
  { value: 9, more_important: "b" as const, label: "çok daha önemli" },
];

type ComparisonState = Record<string, { value: number; more_important: "a" | "b" }>;

interface PersonaFormProps {
  onCreated: (personaId: number) => void;
  onClose: () => void;
}

export default function PersonaForm({ onCreated, onClose }: PersonaFormProps) {
  const [subjectName, setSubjectName] = useState("");
  const [relation, setRelation] = useState("");
  const [age, setAge] = useState("");
  const [dimensions, setDimensions] = useState<Record<string, string>>(
    Object.fromEntries(DIMENSION_KEYS.map((k) => [k, ""]))
  );
  const [comparisons, setComparisons] = useState<ComparisonState>(
    Object.fromEntries(
      COMPARISON_PAIRS.map(([a, b]) => [`${a}|${b}`, { value: 1, more_important: "a" as const }])
    )
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateComparison(pairKey: string, stepIndex: number) {
    const step = SCALE_STEPS[stepIndex];
    setComparisons((prev) => ({
      ...prev,
      [pairKey]: { value: step.value, more_important: step.more_important },
    }));
  }

  async function handleSubmit() {
    setError(null);

    if (!subjectName.trim() || !relation.trim()) {
      setError("İsim ve ilişki (ör. anneanne, dede) zorunlu.");
      return;
    }
    const missingDim = DIMENSION_KEYS.find((k) => !dimensions[k].trim());
    if (missingDim) {
      setError(`"${DIMENSION_LABELS[missingDim]}" boyutu boş bırakılamaz.`);
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/profile/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject_name: subjectName,
          relation,
          age_at_reference: age ? parseInt(age, 10) : null,
          dimensions,
          comparisons: COMPARISON_PAIRS.map(([a, b]) => ({
            a,
            b,
            value: comparisons[`${a}|${b}`].value,
            more_important: comparisons[`${a}|${b}`].more_important,
          })),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Persona oluşturulamadı.");
        return;
      }
      onCreated(data.id);
    } catch (e) {
      setError("Backend'e ulaşılamadı.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold text-slate-800">Yeni Persona Oluştur</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl leading-none">
            ×
          </button>
        </div>

        {/* Temel bilgiler */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          <input
            className="col-span-2 border border-slate-300 rounded-lg px-3 py-2 text-sm"
            placeholder="İsim (ör. Nezahat Yılmaz)"
            value={subjectName}
            onChange={(e) => setSubjectName(e.target.value)}
          />
          <input
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            placeholder="Yaş"
            type="number"
            value={age}
            onChange={(e) => setAge(e.target.value)}
          />
          <input
            className="col-span-3 border border-slate-300 rounded-lg px-3 py-2 text-sm"
            placeholder="İlişki (ör. anneanne, dede, baba)"
            value={relation}
            onChange={(e) => setRelation(e.target.value)}
          />
        </div>

        {/* 5 boyut */}
        <h3 className="text-sm font-semibold text-slate-700 mb-2">Davranışsal Boyutlar</h3>
        <div className="space-y-3 mb-6">
          {DIMENSION_KEYS.map((key) => (
            <div key={key}>
              <label className="text-xs text-slate-500 mb-1 block">{DIMENSION_LABELS[key]}</label>
              <textarea
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                rows={2}
                value={dimensions[key]}
                onChange={(e) => setDimensions((prev) => ({ ...prev, [key]: e.target.value }))}
                placeholder={`${DIMENSION_LABELS[key]} hakkında birkaç cümle yaz...`}
              />
            </div>
          ))}
        </div>

        {/* AHP ikili karşılaştırmalar */}
        <h3 className="text-sm font-semibold text-slate-700 mb-1">
          İkili Karşılaştırmalar (AHP)
        </h3>
        <p className="text-xs text-slate-500 mb-3">
          Her satırda, bu kişiyi tanımlarken hangi boyutun diğerine göre daha belirleyici
          olduğunu seç.
        </p>
        <div className="space-y-3 mb-6">
          {COMPARISON_PAIRS.map(([a, b]) => {
            const pairKey = `${a}|${b}`;
            const current = comparisons[pairKey];
            const currentIndex = SCALE_STEPS.findIndex(
              (s) => s.value === current.value && s.more_important === current.more_important
            );
            return (
              <div key={pairKey} className="text-sm">
                <div className="flex justify-between text-xs text-slate-600 mb-1">
                  <span className={current.more_important === "a" ? "font-semibold" : ""}>
                    {DIMENSION_LABELS[a]}
                  </span>
                  <span className={current.more_important === "b" ? "font-semibold" : ""}>
                    {DIMENSION_LABELS[b]}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={8}
                  step={1}
                  value={currentIndex}
                  onChange={(e) => updateComparison(pairKey, parseInt(e.target.value, 10))}
                  className="w-full accent-blue-600"
                />
                <div className="text-center text-xs text-slate-400">
                  {current.more_important === "a" ? DIMENSION_LABELS[a] : DIMENSION_LABELS[b]}{" "}
                  {SCALE_STEPS[currentIndex].label}
                </div>
              </div>
            );
          })}
        </div>

        {error && <div className="text-red-600 text-sm mb-3">{error}</div>}

        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg text-slate-600 hover:bg-slate-100"
          >
            Vazgeç
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? "Hesaplanıyor..." : "Persona Oluştur"}
          </button>
        </div>
      </div>
    </div>
  );
}