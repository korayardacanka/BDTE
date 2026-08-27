import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// NOTE: these labels and ordering must match backend/app/persona.py's
// DIMENSION_LABELS / COMPARISON_PAIRS exactly.
const DIMENSION_LABELS: Record<string, string> = {
  emotional_patterns: "Emotional patterns",
  communication_style: "Communication style",
  life_preferences: "Life preferences",
  decision_making_traits: "Decision-making traits",
  relationship_dynamics: "Relationship dynamics",
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

// Saaty scale — 9 steps, symmetric (left side favors A, right side favors B).
const SCALE_STEPS = [
  { value: 9, more_important: "a" as const, label: "much more important" },
  { value: 7, more_important: "a" as const, label: "strongly more important" },
  { value: 5, more_important: "a" as const, label: "moderately more important" },
  { value: 3, more_important: "a" as const, label: "slightly more important" },
  { value: 1, more_important: "a" as const, label: "equally important" },
  { value: 3, more_important: "b" as const, label: "slightly more important" },
  { value: 5, more_important: "b" as const, label: "moderately more important" },
  { value: 7, more_important: "b" as const, label: "strongly more important" },
  { value: 9, more_important: "b" as const, label: "much more important" },
];

type ComparisonState = Record<string, { value: number; more_important: "a" | "b" }>;

const defaultComparisons = (): ComparisonState =>
  Object.fromEntries(
    COMPARISON_PAIRS.map(([a, b]) => [`${a}|${b}`, { value: 1, more_important: "a" as const }])
  );

interface PersonaFormProps {
  personaId?: number; // if given, edit mode
  onSaved: (personaId: number) => void;
  onClose: () => void;
}

export default function PersonaForm({ personaId, onSaved, onClose }: PersonaFormProps) {
  const isEditMode = personaId !== undefined;

  const [subjectName, setSubjectName] = useState("");
  const [relation, setRelation] = useState("");
  const [gender, setGender] = useState<"female" | "male">("female");
  const [age, setAge] = useState("");
  const [dimensions, setDimensions] = useState<Record<string, string>>(
    Object.fromEntries(DIMENSION_KEYS.map((k) => [k, ""]))
  );
  const [comparisons, setComparisons] = useState<ComparisonState>(defaultComparisons());
  const [submitting, setSubmitting] = useState(false);
  const [loadingExisting, setLoadingExisting] = useState(isEditMode);
  const [error, setError] = useState<string | null>(null);

  // In edit mode, fetch the existing persona and pre-fill the form.
  useEffect(() => {
    if (!isEditMode) return;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/profile/${personaId}`);
        if (!res.ok) throw new Error("Failed to load persona");
        const data = await res.json();
        setSubjectName(data.subject_name);
        setRelation(data.relation ?? "");
        setGender(data.gender ?? "female");
        setAge(data.age_at_reference ? String(data.age_at_reference) : "");
        setDimensions(data.dimensions ?? {});
        if (data.comparisons) {
          const restored: ComparisonState = {};
          for (const c of data.comparisons) {
            restored[`${c.a}|${c.b}`] = { value: c.value, more_important: c.more_important };
          }
          setComparisons(restored);
        }
      } catch (e) {
        setError("Could not load the existing persona data.");
      } finally {
        setLoadingExisting(false);
      }
    })();
  }, [isEditMode, personaId]);

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
      setError("Name and relation (e.g. grandmother, grandfather) are required.");
      return;
    }
    const missingDim = DIMENSION_KEYS.find((k) => !dimensions[k]?.trim());
    if (missingDim) {
      setError(`"${DIMENSION_LABELS[missingDim]}" cannot be left empty.`);
      return;
    }

    setSubmitting(true);
    try {
      const url = isEditMode ? `${API_BASE}/api/profile/${personaId}` : `${API_BASE}/api/profile/`;
      const method = isEditMode ? "PUT" : "POST";
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject_name: subjectName,
          relation,
          gender,
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
        setError(data.detail || "Operation failed.");
        return;
      }
      if (!data.consistency_ok) {
        alert(
          `Note: the pairwise comparisons you entered came out inconsistent (Consistency Ratio: ${data.consistency_ratio.toFixed(
            3
          )}, target: <0.10). The persona was saved anyway, but for a more reliable result you may want to review the comparisons.`
        );
      }
      onSaved(data.id);
    } catch (e) {
      setError("Could not reach the backend.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loadingExisting) {
    return (
      <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-xl p-6 text-sm text-slate-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold text-slate-800">
            {isEditMode ? "Edit Persona" : "Create New Persona"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl leading-none">
            ×
          </button>
        </div>

        <div className="grid grid-cols-3 gap-3 mb-5">
          <input
            className="col-span-2 border border-slate-300 rounded-lg px-3 py-2 text-sm"
            placeholder="Name (e.g. Margaret Whitfield)"
            value={subjectName}
            onChange={(e) => setSubjectName(e.target.value)}
          />
          <input
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            placeholder="Age"
            type="number"
            value={age}
            onChange={(e) => setAge(e.target.value)}
          />
          <input
            className="col-span-2 border border-slate-300 rounded-lg px-3 py-2 text-sm"
            placeholder="Relation (e.g. grandmother, grandfather, father)"
            value={relation}
            onChange={(e) => setRelation(e.target.value)}
          />
          <div className="flex items-center gap-3 text-sm text-slate-600 border border-slate-300 rounded-lg px-3 py-2">
            <label className="flex items-center gap-1 cursor-pointer">
              <input type="radio" checked={gender === "female"} onChange={() => setGender("female")} />
              Female
            </label>
            <label className="flex items-center gap-1 cursor-pointer">
              <input type="radio" checked={gender === "male"} onChange={() => setGender("male")} />
              Male
            </label>
          </div>
        </div>

        <h3 className="text-sm font-semibold text-slate-700 mb-2">Behavioral Dimensions</h3>
        <div className="space-y-3 mb-6">
          {DIMENSION_KEYS.map((key) => (
            <div key={key}>
              <label className="text-xs text-slate-500 mb-1 block">{DIMENSION_LABELS[key]}</label>
              <textarea
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                rows={2}
                value={dimensions[key] || ""}
                onChange={(e) => setDimensions((prev) => ({ ...prev, [key]: e.target.value }))}
                placeholder={`Write a few sentences about ${DIMENSION_LABELS[key].toLowerCase()}...`}
              />
            </div>
          ))}
        </div>

        <h3 className="text-sm font-semibold text-slate-700 mb-1">Pairwise Comparisons (AHP)</h3>
        <p className="text-xs text-slate-500 mb-3">
          For each row, choose which dimension is more defining of this person compared to the other.
        </p>
        <div className="space-y-3 mb-6">
          {COMPARISON_PAIRS.map(([a, b]) => {
            const pairKey = `${a}|${b}`;
            const current = comparisons[pairKey];
            let currentIndex = SCALE_STEPS.findIndex(
              (s) => s.value === current.value && s.more_important === current.more_important
            );
            // Defensive fallback: if the stored value doesn't exactly match a
            // slider step (e.g. data from an external source using the full
            // 1-9 Saaty scale instead of just 1/3/5/7/9), snap to the closest
            // step instead of crashing on an invalid array index.
            if (currentIndex === -1) {
              const signedValue = current.more_important === "a" ? current.value : -current.value;
              let closest = 0;
              let closestDiff = Infinity;
              SCALE_STEPS.forEach((s, i) => {
                const sSigned = s.more_important === "a" ? s.value : -s.value;
                const diff = Math.abs(sSigned - signedValue);
                if (diff < closestDiff) {
                  closestDiff = diff;
                  closest = i;
                }
              });
              currentIndex = closest;
            }
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
                  is {SCALE_STEPS[currentIndex].label}
                </div>
              </div>
            );
          })}
        </div>

        {error && <div className="text-red-600 text-sm mb-3">{error}</div>}

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg text-slate-600 hover:bg-slate-100">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? "Computing..." : isEditMode ? "Save" : "Create Persona"}
          </button>
        </div>
      </div>
    </div>
  );
}