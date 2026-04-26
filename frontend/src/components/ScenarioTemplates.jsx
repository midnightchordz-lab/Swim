import React from "react";
import { Target } from "lucide-react";

export const SCENARIO_TEMPLATES = [
  {
    id: "finance",
    title: "Financial Decision Support",
    icon: "FIN",
    topic: "Nvidia stock outlook",
    horizon: "Next month",
    query: "Will investor sentiment around Nvidia strengthen or weaken over the next month?",
    description: "Investor sentiment, market signals, risk factors, and strategy rehearsal.",
  },
  {
    id: "policy",
    title: "Policy Opinion Forecasting",
    icon: "GOV",
    topic: "AI regulation in Europe",
    horizon: "Next 3 months",
    query: "How will public and stakeholder reactions evolve around new AI regulation?",
    description: "Forecast public response, stakeholder coalitions, and policy risk points.",
  },
  {
    id: "crisis",
    title: "Crisis PR Simulation",
    icon: "PR",
    topic: "Brand product recall crisis",
    horizon: "Next week",
    query: "How will online sentiment and influencer reactions evolve after a product recall?",
    description: "Stress-test messaging, escalation paths, and reputational contagion.",
  },
  {
    id: "marketing",
    title: "Marketing Strategy Testing",
    icon: "MKT",
    topic: "New electric scooter launch",
    horizon: "Next month",
    query: "Which user groups are most likely to amplify or reject this launch campaign?",
    description: "Test campaign resonance, objections, and audience segmentation.",
  },
  {
    id: "fiction",
    title: "Story and Fiction Deduction",
    icon: "STO",
    topic: "Lost ending of a mystery novel",
    horizon: "Long term (1+ year)",
    query: "What is the most plausible ending based on character motives and unresolved conflicts?",
    description: "Simulate character worlds, relationship dynamics, and possible endings.",
  },
  {
    id: "research",
    title: "Academic Research Support",
    icon: "LAB",
    topic: "Misinformation spread in local communities",
    horizon: "Next 6 months",
    query: "How might misinformation spread across groups under different trust conditions?",
    description: "Controlled social simulation for information propagation and group behavior.",
  },
];

const ScenarioTemplates = ({ selectedId, onSelect }) => (
  <div data-testid="scenario-templates" className="glass-card" style={{ padding: "16px", marginBottom: "18px" }}>
    <div className="flex items-center gap-2 mb-3">
      <Target className="w-4 h-4 text-sw-cyan" />
      <div>
        <h3 className="text-sm font-bold text-sw">Scenario Templates</h3>
        <p className="text-xs text-sw2">Pick a MiroFish-style scenario to prefill the prediction setup.</p>
      </div>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
      {SCENARIO_TEMPLATES.map((template) => (
        <button
          key={template.id}
          type="button"
          onClick={() => onSelect(template)}
          className={`text-left rounded-xl border p-3 transition-all ${
            selectedId === template.id ? "border-sw-cyan bg-sw-cyan/10" : "border-sw bg-sw3/40 hover:border-sw-cyan/60"
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">{template.icon}</span>
            <span className="text-xs font-semibold text-sw">{template.title}</span>
          </div>
          <p className="text-[11px] text-sw2 leading-relaxed">{template.description}</p>
        </button>
      ))}
    </div>
  </div>
);

export default ScenarioTemplates;
