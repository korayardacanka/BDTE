interface WeightChartProps {
  weights: Record<string, number>;
}

const DIMENSION_LABELS: Record<string, string> = {
  emotional_patterns: "Emotional patterns",
  communication_style: "Communication style",
  life_preferences: "Life preferences",
  decision_making_traits: "Decision-making traits",
  relationship_dynamics: "Relationship dynamics",
};

const BAR_COLORS = ["#2563eb", "#7c3aed", "#db2777", "#ea580c", "#16a34a"];

/**
 * Simple horizontal bar chart showing the AHP-derived weight of each
 * behavioral dimension for the currently selected persona. Built with
 * plain CSS (no charting library) to keep the bundle small.
 */
export default function WeightChart({ weights }: WeightChartProps) {
  const entries = Object.entries(weights).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return null;

  const maxWeight = Math.max(...entries.map(([, w]) => w));

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-4">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
        AHP Weights
      </h3>
      <div className="space-y-2">
        {entries.map(([key, weight], i) => (
          <div key={key}>
            <div className="flex justify-between text-xs text-slate-600 mb-0.5">
              <span>{DIMENSION_LABELS[key] ?? key}</span>
              <span className="font-medium">{(weight * 100).toFixed(1)}%</span>
            </div>
            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${(weight / maxWeight) * 100}%`,
                  backgroundColor: BAR_COLORS[i % BAR_COLORS.length],
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}