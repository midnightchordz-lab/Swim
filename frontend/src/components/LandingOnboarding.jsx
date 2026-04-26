import React from "react";
import { ArrowRight, Sparkles } from "lucide-react";

const steps = [
  ["01", "Graph Construction", "Extract seed reality, entities, relationships, and memory context."],
  ["02", "Environment Setup", "Generate personas, configure population scale, and tune simulation parameters."],
  ["03", "Start Simulation", "Run parallel social worlds where agents react, debate, and shift beliefs."],
  ["04", "Report Generation", "Analyze the post-simulation world with evidence, risk, and scenario branches."],
  ["05", "Deep Interaction", "Chat with agents or the ReportAgent to probe why outcomes emerged."],
];

const LandingOnboarding = ({ onStart }) => (
  <section className="mb-8 rounded-2xl border border-sw bg-panel overflow-hidden">
    <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-6 p-6 md:p-8">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs mono mb-4" style={{background:'var(--cyan-dim)',color:'var(--cyan)',border:'1px solid var(--border-bright)'}}>
          <Sparkles className="w-3.5 h-3.5" />
          PREDICTA DECISION INTELLIGENCE ENGINE
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold mb-4" style={{fontFamily:'var(--display)',color:'var(--text)'}}>
          Predict Anything
        </h1>
        <p className="text-base md:text-lg max-w-2xl mb-6" style={{color:'var(--text2)',lineHeight:1.7}}>
          Build a high-fidelity digital sandbox from live data, documents, or creative worlds. Then rehearse futures with agent societies, variable injection, and evidence-aware reports.
        </p>
        <div className="flex flex-wrap gap-3">
          <button className="btn-primary" style={{width:'auto',padding:'12px 18px'}} onClick={onStart}>
            Start Simulation
            <ArrowRight className="w-4 h-4" />
          </button>
          <span className="inline-flex items-center px-3 py-2 rounded-lg text-xs" style={{background:'var(--bg3)',color:'var(--text2)',border:'1px solid var(--border)'}}>
            GraphRAG-inspired memory · persona swarms · ReportAgent analysis
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2">
        {steps.map(([num, title, desc]) => (
          <div key={num} className="rounded-xl p-3 border border-sw" style={{background:'rgba(15,21,37,0.62)'}}>
            <div className="flex gap-3">
              <span className="mono text-xs mt-0.5" style={{color:'var(--cyan)'}}>{num}</span>
              <div>
                <p className="text-sm font-bold text-sw">{title}</p>
                <p className="text-xs text-sw2 leading-relaxed">{desc}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  </section>
);

export default LandingOnboarding;
