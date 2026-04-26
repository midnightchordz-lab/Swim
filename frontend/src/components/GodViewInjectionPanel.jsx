import React, { useState } from "react";
import axios from "axios";
import { Loader2, PlusCircle, Zap } from "lucide-react";

const suggestions = [
  "A major influencer publicly endorses the opposing view",
  "Fresh market data contradicts the dominant narrative",
  "A regulator announces an unexpected investigation",
  "A leaked memo reframes the public debate",
];

const GodViewInjectionPanel = ({ apiBase, sessionId, onInjected }) => {
  const [variable, setVariable] = useState("");
  const [rounds, setRounds] = useState(2);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const inject = async () => {
    if (!variable.trim() || loading) return;
    setLoading(true);
    setMessage(null);
    try {
      const response = await axios.post(`${apiBase}/sessions/${sessionId}/inject-variable`, {
        variable: variable.trim(),
        num_new_rounds: rounds,
      });
      setMessage({
        type: "success",
        text: `Injected new development and generated ${response.data.new_rounds} round(s).`,
      });
      setVariable("");
      onInjected?.(response.data);
    } catch (err) {
      setMessage({
        type: "error",
        text: err.response?.data?.detail || "Failed to inject variable",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="god-view-injection-panel" className="bg-panel border border-sw rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Zap className="w-4 h-4 text-amber-400" />
        <h3 className="text-sm font-bold text-sw">God-View Variable Injection</h3>
      </div>
      <p className="text-xs text-sw2 mb-3">
        Add a new development after the simulation and let agents react in fresh rounds.
      </p>

      <textarea
        data-testid="inject-variable-input"
        className="w-full min-h-[86px] px-3 py-2 bg-sw-bg3 border border-sw rounded-lg text-sw text-sm placeholder:text-sw3 focus:outline-none focus:border-sw-cyan"
        value={variable}
        onChange={(event) => setVariable(event.target.value)}
        placeholder="Example: A surprise court ruling changes the policy timeline..."
      />

      <div className="flex flex-wrap gap-2 my-3">
        {suggestions.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setVariable(item)}
            className="text-[10px] px-2 py-1 rounded-full border border-sw text-sw2 hover:text-sw-cyan hover:border-sw-cyan transition-colors"
          >
            {item}
          </button>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
        <label className="text-xs text-sw2 flex items-center gap-2">
          New rounds
          <input
            data-testid="inject-rounds-input"
            type="number"
            min="1"
            max="5"
            value={rounds}
            onChange={(event) => setRounds(Math.max(1, Math.min(5, Number(event.target.value) || 1)))}
            className="w-16 px-2 py-1 bg-sw-bg3 border border-sw rounded text-sw text-xs"
          />
        </label>
        <button
          data-testid="inject-variable-button"
          onClick={inject}
          disabled={!variable.trim() || loading}
          className="btn-primary sm:flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlusCircle className="w-4 h-4" />}
          Inject Development
        </button>
      </div>

      {message && (
        <p className={`mt-3 text-xs ${message.type === "success" ? "text-sw-cyan" : "text-red-400"}`}>
          {message.text}
        </p>
      )}
    </div>
  );
};

export default GodViewInjectionPanel;
