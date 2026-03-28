import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import axios from "axios";
import ForceGraph2D from "react-force-graph-2d";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";
import {
  Upload, FileText, Users, Play, BarChart3, MessageSquare,
  CheckCircle, Loader2, ArrowRight, Send, AlertCircle,
  Twitter, ChevronRight, Zap, Target, TrendingUp, AlertTriangle,
  Download, RefreshCw, Eye, EyeOff, Settings, Terminal,
  Globe, Radio, Clock, Wifi, PlusCircle, Sparkles, Shield
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip as ReTooltip,
  ResponsiveContainer, CartesianGrid,
} from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Prediction horizons
const PREDICTION_HORIZONS = [
  "Next 24 hours",
  "Next week",
  "Next month",
  "Next 3 months",
  "Next 6 months",
  "Long term (1+ year)"
];

// Skeleton Component
const Skeleton = ({ className = "" }) => (
  <div className={`animate-pulse bg-gray-800 rounded ${className}`} />
);

// Skeleton Card Component
const SkeletonCard = () => (
  <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
    <div className="flex items-center gap-4">
      <Skeleton className="w-12 h-12 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
    <Skeleton className="h-20 w-full" />
    <div className="flex gap-2">
      <Skeleton className="h-6 w-20 rounded-full" />
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
  </div>
);

// Skeleton Grid Component
const SkeletonGrid = ({ count = 4 }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="bg-gray-900 border border-gray-800 rounded-lg p-4 space-y-3">
        <Skeleton className="w-10 h-10 rounded-full mx-auto" />
        <Skeleton className="h-4 w-3/4 mx-auto" />
        <Skeleton className="h-3 w-1/2 mx-auto" />
      </div>
    ))}
  </div>
);

// Particle Background Component
const ParticleBackground = () => {
  const [init, setInit] = useState(false);

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => {
      setInit(true);
    });
  }, []);

  const particlesOptions = useMemo(() => ({
    background: {
      color: { value: "transparent" },
    },
    fpsLimit: 60,
    particles: {
      color: { value: ["#3b82f6", "#8b5cf6", "#06b6d4", "#10b981"] },
      links: {
        color: "#3b82f6",
        distance: 150,
        enable: true,
        opacity: 0.1,
        width: 1,
      },
      move: {
        enable: true,
        speed: 0.5,
        direction: "none",
        random: true,
        straight: false,
        outModes: { default: "out" },
      },
      number: {
        density: { enable: true, area: 1000 },
        value: 60,
      },
      opacity: {
        value: { min: 0.1, max: 0.4 },
        animation: {
          enable: true,
          speed: 1,
          minimumValue: 0.1,
        },
      },
      shape: { type: "circle" },
      size: {
        value: { min: 1, max: 3 },
      },
    },
    detectRetina: true,
  }), []);

  if (!init) return null;

  return (
    <Particles
      id="tsparticles"
      options={particlesOptions}
      className="absolute inset-0 pointer-events-none"
    />
  );
};

// Entity type colors
const ENTITY_COLORS = {
  person: "#f97316",
  organization: "#3b82f6",
  faction: "#a855f7",
  concept: "#22c55e",
  event: "#ef4444",
  default: "#6b7280"
};

// Step definitions
const STEPS = [
  { id: 1, name: "Upload Seed", icon: FileText, emoji: "📄" },
  { id: 2, name: "Generate Agents", icon: Users, emoji: "🤖" },
  { id: 3, name: "Simulate", icon: Play, emoji: "🌊" },
  { id: 4, name: "Report", icon: BarChart3, emoji: "📊" },
  { id: 5, name: "Interact", icon: MessageSquare, emoji: "💬" },
];

// Personality colors mapping
const PERSONALITY_COLORS = {
  Skeptic: "badge-skeptic",
  Optimist: "badge-optimist",
  Insider: "badge-insider",
  Contrarian: "badge-contrarian",
  Expert: "badge-expert",
  Activist: "badge-activist",
  Pragmatist: "badge-pragmatist",
  Neutral: "badge-neutral",
};

// Header Component
const EmotionalTemperatureGauge = ({ data }) => {
  if (!data) return null;
  const { state, mean_valence, mean_arousal } = data;
  const stateColors = {
    PANIC: "bg-red-500/20 text-red-400 border-red-500/40",
    fear: "bg-orange-500/20 text-orange-400 border-orange-500/40",
    agitated: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
    calm: "bg-gray-500/20 text-gray-400 border-gray-500/40",
    optimism: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
    EUPHORIA: "bg-cyan-500/20 text-cyan-400 border-cyan-500/40",
  };
  const colorClass = stateColors[state] || stateColors.calm;
  return (
    <div data-testid="emotional-temperature" className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${colorClass}`}>
      <span className="uppercase tracking-wider">{state}</span>
      <span className="opacity-70">V:{mean_valence > 0 ? "+" : ""}{mean_valence?.toFixed(2)} A:{mean_arousal?.toFixed(2)}</span>
    </div>
  );
};

const SentimentChart = ({ posts }) => {
  if (!posts || posts.length === 0) return null;
  const rounds = {};
  posts.forEach(p => {
    const r = p.round;
    if (!rounds[r]) rounds[r] = { round: r, positive: 0, negative: 0, neutral: 0, total: 0 };
    const v = p.belief_position || p.emotional_valence || 0;
    if (v > 0.15) rounds[r].positive++;
    else if (v < -0.15) rounds[r].negative++;
    else rounds[r].neutral++;
    rounds[r].total++;
  });
  const chartData = Object.values(rounds).sort((a, b) => a.round - b.round).map(r => ({
    name: `R${r.round}`,
    positive: r.total ? Math.round((r.positive / r.total) * 100) : 0,
    negative: r.total ? Math.round((r.negative / r.total) * 100) : 0,
    neutral: r.total ? Math.round((r.neutral / r.total) * 100) : 0,
  }));
  if (chartData.length < 2) return null;
  return (
    <div data-testid="sentiment-chart" className="bg-gray-900/50 rounded-xl p-4 border border-gray-800">
      <p className="text-xs text-gray-400 uppercase tracking-wider mb-3">Sentiment Flow by Round</p>
      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="name" tick={{ fill: "#888", fontSize: 11 }} />
          <YAxis tick={{ fill: "#888", fontSize: 11 }} domain={[0, 100]} />
          <ReTooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #333", borderRadius: 8 }} />
          <Area type="monotone" dataKey="positive" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
          <Area type="monotone" dataKey="neutral" stackId="1" stroke="#6b7280" fill="#6b7280" fillOpacity={0.4} />
          <Area type="monotone" dataKey="negative" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.6} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

const Header = ({ onNewSimulation, hasSession }) => (
  <header className="sticky top-0 z-50 w-full border-b border-gray-800 bg-gray-950/80 backdrop-blur-xl">
    <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between h-14">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🐟</span>
          <div>
            <h1 className="text-lg font-black tracking-tighter text-white">SwarmSim</h1>
            <p className="text-[10px] text-gray-500 tracking-wide">Swarm Intelligence Prediction Engine</p>
          </div>
        </div>
        {hasSession && (
          <button
            data-testid="new-simulation-button"
            onClick={onNewSimulation}
            className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm text-gray-300 hover:text-white transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Simulation</span>
          </button>
        )}
      </div>
    </div>
  </header>
);

// Step Indicator Component
const StepIndicator = ({ currentStep, completedSteps, onStepClick }) => (
  <div className="w-full max-w-3xl mx-auto mb-6 px-4">
    <div className="flex items-center justify-between">
      {STEPS.map((step, index) => {
        const isActive = currentStep === step.id;
        const isCompleted = completedSteps.includes(step.id);
        const isClickable = isCompleted || step.id <= Math.max(...completedSteps, 1);
        
        return (
          <React.Fragment key={step.id}>
            <button
              data-testid={`step-${step.id}-indicator`}
              onClick={() => isClickable && onStepClick(step.id)}
              disabled={!isClickable}
              className={`flex flex-col items-center gap-1.5 transition-all duration-200 ${
                isClickable ? "cursor-pointer" : "cursor-not-allowed opacity-50"
              }`}
            >
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center border-2 transition-all ${
                  isActive
                    ? "border-blue-500 bg-blue-500/20 text-blue-400"
                    : isCompleted
                    ? "border-emerald-500 bg-emerald-500/20 text-emerald-400"
                    : "border-gray-700 bg-gray-900 text-gray-500"
                }`}
              >
                {isCompleted && !isActive ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <span className="text-base">{step.emoji}</span>
                )}
              </div>
              <span
                className={`text-[10px] font-medium hidden sm:block ${
                  isActive ? "text-blue-400" : isCompleted ? "text-emerald-400" : "text-gray-600"
                }`}
              >
                {step.name}
              </span>
            </button>
            {index < STEPS.length - 1 && (
              <div
                className={`flex-1 h-px mx-2 transition-colors ${
                  completedSteps.includes(step.id) ? "bg-emerald-500/50" : "bg-gray-800"
                }`}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  </div>
);

// Knowledge Graph Visualization Component
const KnowledgeGraph = ({ graph, onRefresh }) => {
  const graphRef = useRef();
  const [showLabels, setShowLabels] = useState(true);
  const [dimensions, setDimensions] = useState({ width: 600, height: 500 });
  const containerRef = useRef();

  useEffect(() => {
    if (containerRef.current) {
      const updateDimensions = () => {
        if (containerRef.current) {
          setDimensions({
            width: containerRef.current.offsetWidth,
            height: Math.min(500, window.innerHeight - 300)
          });
        }
      };
      updateDimensions();
      window.addEventListener('resize', updateDimensions);
      return () => window.removeEventListener('resize', updateDimensions);
    }
  }, []);

  const graphData = useMemo(() => {
    if (!graph?.entities) return { nodes: [], links: [] };
    
    const nodes = graph.entities.map((entity, idx) => ({
      id: entity.id,
      name: entity.name,
      type: entity.type,
      stance: entity.stance,
      description: entity.description,
      color: ENTITY_COLORS[entity.type] || ENTITY_COLORS.default,
      val: 8
    }));

    const nodeIds = new Set(nodes.map(n => n.id));
    const links = (graph.relationships || [])
      .filter(rel => nodeIds.has(rel.source) && nodeIds.has(rel.target))
      .map(rel => ({
        source: rel.source,
        target: rel.target,
        label: rel.label,
        weight: rel.weight || 0.5
      }));

    return { nodes, links };
  }, [graph]);

  const entityTypes = useMemo(() => {
    if (!graph?.entities) return [];
    const types = [...new Set(graph.entities.map(e => e.type))];
    return types.map(type => ({
      type,
      color: ENTITY_COLORS[type] || ENTITY_COLORS.default,
      count: graph.entities.filter(e => e.type === type).length
    }));
  }, [graph]);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden h-full flex flex-col">
      <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between bg-gray-950">
        <h3 className="text-sm font-semibold text-white">Graph Relationship Visualization</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="p-1.5 hover:bg-gray-800 rounded transition-colors text-gray-400 hover:text-white"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowLabels(!showLabels)}
            className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors ${
              showLabels ? "bg-blue-500/20 text-blue-400" : "bg-gray-800 text-gray-400"
            }`}
          >
            {showLabels ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
            <span>Edge Labels</span>
          </button>
        </div>
      </div>
      
      <div ref={containerRef} className="flex-1 bg-gray-950 relative">
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="#030712"
          nodeLabel={node => `${node.name}\n${node.description || ''}`}
          nodeColor={node => node.color}
          nodeRelSize={6}
          linkColor={() => "rgba(100, 116, 139, 0.3)"}
          linkWidth={link => Math.max(1, link.weight * 3)}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={2}
          linkDirectionalParticleColor={() => "rgba(59, 130, 246, 0.5)"}
          linkLabel={showLabels ? link => link.label : undefined}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 10 / globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;
            
            // Node circle
            ctx.beginPath();
            ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI);
            ctx.fillStyle = node.color;
            ctx.fill();
            
            // Label
            if (globalScale > 0.5) {
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillStyle = "#fff";
              ctx.fillText(label, node.x, node.y + 12);
            }
          }}
          cooldownTicks={100}
          onEngineStop={() => graphRef.current?.zoomToFit(400, 50)}
        />
      </div>

      {/* Entity Type Legend */}
      <div className="px-4 py-3 border-t border-gray-800 bg-gray-950">
        <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Entity Types</p>
        <div className="flex flex-wrap gap-3">
          {entityTypes.map(({ type, color, count }) => (
            <div key={type} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-xs text-gray-400 capitalize">{type}</span>
              <span className="text-[10px] text-gray-600">({count})</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// System Dashboard Component
const SystemDashboard = ({ logs }) => {
  const logsEndRef = useRef(null);
  
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
      <div className="px-3 py-2 border-b border-gray-800 flex items-center gap-2 bg-gray-950">
        <Terminal className="w-3.5 h-3.5 text-gray-400" />
        <span className="text-xs font-medium text-gray-400">System Dashboard</span>
      </div>
      <div className="h-24 overflow-y-auto p-2 font-mono text-[10px] text-gray-400 bg-gray-950">
        {logs.map((log, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-gray-600">{log.time}</span>
            <span className={log.type === "success" ? "text-emerald-400" : log.type === "error" ? "text-red-400" : "text-gray-400"}>
              {log.message}
            </span>
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

// Upload Step Component with Graph Visualization
const UploadStep = ({ sessionId, onComplete }) => {
  const [mode, setMode] = useState("upload"); // "upload" or "live"
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState("");
  const [topic, setTopic] = useState("");
  const [horizon, setHorizon] = useState("Next month");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [graph, setGraph] = useState(null);
  const [intelBrief, setIntelBrief] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [logs, setLogs] = useState([]);
  const fileInputRef = useRef(null);

  const addLog = (message, type = "info") => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    setLogs(prev => [...prev.slice(-20), { time, message, type }]);
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      addLog(`File selected: ${e.dataTransfer.files[0].name}`, "success");
    }
  }, []);

  const handleUploadSubmit = async () => {
    if (!file || !query.trim()) return;
    setLoading(true);
    setError(null);
    addLog("Starting document processing...");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("prediction_query", query);

    try {
      addLog("Uploading document to server...");
      const response = await axios.post(`${API}/sessions/${sessionId}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      addLog(`Extracted ${response.data.graph.entities?.length || 0} entities`, "success");
      addLog(`Found ${response.data.graph.relationships?.length || 0} relationships`, "success");
      setGraph(response.data.graph);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Failed to process document";
      addLog(`Error: ${errorMsg}`, "error");
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleLiveSubmit = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    addLog(`Fetching live data for: ${topic}...`);
    addLog(`Prediction horizon: ${horizon}`);

    try {
      // Kick off background fetch (returns 202 immediately)
      await axios.post(`${API}/sessions/${sessionId}/fetch-live`, {
        topic: topic,
        horizon: horizon,
        prediction_query: query || `What will happen with ${topic} in the ${horizon.toLowerCase()}?`
      }, { timeout: 15000 });
      
      // Poll for status with progress updates
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await axios.get(`${API}/sessions/${sessionId}/live-status`, { timeout: 10000 });
          const data = statusRes.data;
          
          // Show progress messages in the log
          if (data.progress && data.status === "fetching") {
            addLog(data.progress);
          }
          
          if (data.status === "completed") {
            clearInterval(pollInterval);
            addLog(`Extracted ${data.graph?.entities?.length || 0} entities`, "success");
            addLog(`Found ${data.graph?.relationships?.length || 0} relationships`, "success");
            setGraph(data.graph);
            setIntelBrief(data.intel_brief);
            setLoading(false);
          } else if (data.status === "failed") {
            clearInterval(pollInterval);
            const errMsg = data.error || "Live fetch failed";
            addLog(`Error: ${errMsg}`, "error");
            setError(errMsg);
            setLoading(false);
          }
        } catch (pollErr) {
          // Transient polling error, keep trying
        }
      }, 1500);
      
      // Safety timeout after 3 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (!graph) {
          setError("Live intelligence fetch is taking too long. Please try again.");
          setLoading(false);
        }
      }, 180000);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Failed to start live fetch";
      addLog(`Error: ${errorMsg}`, "error");
      setError(errorMsg);
      setLoading(false);
    }
  };

  const handleSubmit = mode === "upload" ? handleUploadSubmit : handleLiveSubmit;

  const exampleQuestions = [
    "Will public support increase or decrease in 6 months?",
    "What is the market sentiment outlook?",
    "How will policy changes impact stakeholders?",
  ];

  const exampleTopics = [
    "Bitcoin price movement",
    "US Federal Reserve interest rates",
    "AI regulation in Europe",
    "Tesla stock outlook",
  ];

  if (graph) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in">
        {/* Left: Knowledge Graph */}
        <div className="h-[600px]">
          <KnowledgeGraph graph={graph} onRefresh={() => {}} />
        </div>

        {/* Right: Summary & Actions */}
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-4">
              {mode === "live" ? (
                <Radio className="w-5 h-5 text-green-400 animate-pulse" />
              ) : (
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              )}
              <h3 className="text-lg font-bold text-white">
                {mode === "live" ? "Live Intelligence Brief" : "Knowledge Graph Extracted"}
              </h3>
              {mode === "live" && (
                <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-[10px] rounded-full border border-green-500/30 animate-pulse">
                  LIVE
                </span>
              )}
            </div>
            
            <p className="text-gray-300 text-sm mb-4">{graph.summary}</p>
            
            {/* Intel Brief Details for Live Mode */}
            {mode === "live" && intelBrief && (
              <div className="mb-4 space-y-3">
                {intelBrief.key_developments && (
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Key Developments</p>
                    <ul className="space-y-1">
                      {intelBrief.key_developments.slice(0, 3).map((dev, i) => (
                        <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                          <span className="text-green-400">•</span> {dev}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {intelBrief.data_points && intelBrief.data_points.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {intelBrief.data_points.slice(0, 3).map((dp, i) => (
                      <div key={i} className="px-2 py-1 bg-gray-950 rounded border border-gray-800">
                        <span className="text-[10px] text-gray-500">{dp.metric}:</span>
                        <span className="text-xs text-white ml-1">{dp.value}</span>
                        <span className={`text-[10px] ml-1 ${dp.trend === 'up' ? 'text-green-400' : dp.trend === 'down' ? 'text-red-400' : 'text-gray-400'}`}>
                          {dp.trend === 'up' ? '↑' : dp.trend === 'down' ? '↓' : '→'}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Verified Market Data for Live Mode */}
            {mode === "live" && intelBrief?.verified_market_data && intelBrief.verified_market_data.length > 0 && (
              <div data-testid="verified-market-data" className="mb-4 bg-gray-950 rounded-xl p-3 border border-emerald-500/30">
                <p className="text-xs text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <CheckCircle className="w-3 h-3" /> Verified Real-Time Data
                </p>
                <div className="space-y-2">
                  {intelBrief.verified_market_data.map((md, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span className="text-sm text-white font-medium">{md.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-white mono">{md.currency} {md.price?.toLocaleString()}</span>
                        {md.change_pct != null && (
                          <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${md.change_pct >= 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                            {md.change_pct >= 0 ? '+' : ''}{md.change_pct}%
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex flex-wrap gap-2 mb-5">
              {graph.themes?.map((theme, i) => (
                <span key={i} className="px-2.5 py-1 bg-blue-500/10 text-blue-400 text-xs rounded-full border border-blue-500/20">
                  {theme}
                </span>
              ))}
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-950 rounded-lg p-3 border border-gray-800">
                <div className="text-2xl font-bold text-blue-400 mono">{graph.entities?.length || 0}</div>
                <div className="text-xs text-gray-400">Entities</div>
              </div>
              <div className="bg-gray-950 rounded-lg p-3 border border-gray-800">
                <div className="text-2xl font-bold text-emerald-400 mono">{graph.relationships?.length || 0}</div>
                <div className="text-xs text-gray-400">Relationships</div>
              </div>
            </div>
          </div>

          {/* Entity Preview */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 max-h-48 overflow-y-auto">
            <h4 className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wider">Key Entities</h4>
            <div className="space-y-2">
              {graph.entities?.slice(0, 6).map((entity, i) => (
                <div key={i} className="flex items-center gap-2 p-2 bg-gray-950 rounded border border-gray-800">
                  <div 
                    className="w-2 h-2 rounded-full flex-shrink-0" 
                    style={{ backgroundColor: ENTITY_COLORS[entity.type] || ENTITY_COLORS.default }}
                  />
                  <span className="text-white text-sm font-medium truncate">{entity.name}</span>
                  <span className="text-[10px] text-gray-500 capitalize ml-auto">{entity.type}</span>
                </div>
              ))}
            </div>
          </div>

          <SystemDashboard logs={logs} />
          
          <button
            data-testid="continue-to-agents-button"
            onClick={() => onComplete(graph)}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            Continue → Generate Agents
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-8 relative">
        {/* Gradient orbs background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-20 -left-20 w-80 h-80 bg-blue-500/30 rounded-full blur-3xl animate-pulse" />
          <div className="absolute -top-10 -right-20 w-72 h-72 bg-purple-500/30 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute top-10 left-1/2 w-56 h-56 bg-cyan-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        </div>
        
        <div className="relative">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-full mb-4">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            <span className="text-xs font-medium text-blue-300">AI-Powered Prediction Engine</span>
          </div>
          
          <h2 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-blue-100 to-purple-200 mb-3">
            {mode === "live" ? "Live Intelligence Mode" : "Upload Your Seed Document"}
          </h2>
          <p className="text-gray-400 text-base max-w-lg mx-auto">
            {mode === "live" 
              ? "Fetch real-time data from the web and simulate market reactions."
              : "Feed the swarm with data. Our AI agents will analyze, debate, and predict outcomes."
            }
          </p>
        </div>
      </div>

      {/* Mode Toggle */}
      <div className="flex justify-center mb-6">
        <div className="inline-flex bg-gray-900 border border-gray-800 rounded-xl p-1">
          <button
            data-testid="mode-upload"
            onClick={() => setMode("upload")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              mode === "upload"
                ? "bg-blue-600 text-white shadow-lg"
                : "text-gray-400 hover:text-white"
            }`}
          >
            <Upload className="w-4 h-4" />
            Document Upload
          </button>
          <button
            data-testid="mode-live"
            onClick={() => setMode("live")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              mode === "live"
                ? "bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg"
                : "text-gray-400 hover:text-white"
            }`}
          >
            <Radio className="w-4 h-4" />
            Live Intelligence
            <span className="px-1.5 py-0.5 bg-green-500/20 text-green-400 text-[10px] rounded-full">NEW</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Card */}
      <div className="relative group">
        <div className={`absolute -inset-0.5 bg-gradient-to-r ${mode === "live" ? "from-green-500 via-emerald-500 to-cyan-500" : "from-blue-500 via-purple-500 to-emerald-500"} rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500`} />
        <div className="relative bg-gray-900/90 backdrop-blur-xl border border-gray-800 rounded-2xl p-8">
          
          {mode === "upload" ? (
            /* Upload Mode Content */
            <>
              <div
                data-testid="upload-dropzone"
                onClick={() => fileInputRef.current?.click()}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300 ${
                  dragActive
                    ? "border-blue-400 bg-blue-500/10 scale-[1.02]"
                    : file
                    ? "border-emerald-400 bg-emerald-500/10"
                    : "border-gray-600 hover:border-blue-400 bg-gray-950/50 hover:bg-blue-500/5"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt,.docx,.md,.png,.jpg,.jpeg,.webp,.gif"
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      setFile(e.target.files[0]);
                      addLog(`File selected: ${e.target.files[0].name}`, "success");
                    }
                  }}
                  className="hidden"
                />
                {file ? (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center">
                      <FileText className="w-8 h-8 text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-white font-semibold text-lg">{file.name}</p>
                      <p className="text-sm text-emerald-400">{(file.size / 1024).toFixed(1)} KB • Ready to process</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-4">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center border border-blue-500/20">
                      <Upload className="w-10 h-10 text-blue-400" />
                    </div>
                    <div>
                      <p className="text-white font-semibold text-lg mb-1">Drop your file here or click to browse</p>
                      <p className="text-sm text-gray-500">PDF, TXT, DOCX, MD, or Images (max 10MB)</p>
                    </div>
                    <div className="flex flex-wrap justify-center gap-2 mt-2">
                      {['📄 PDF', '📝 TXT', '📊 DOCX', '🖼️ Images'].map((type) => (
                        <span key={type} className="px-3 py-1 bg-gray-800/50 text-gray-400 text-xs rounded-full">
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Prediction Question */}
              <div className="mt-6">
                <label className="block text-sm font-semibold text-white mb-2">
                  🎯 Prediction Question
                </label>
                <textarea
                  data-testid="prediction-query-input"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="What do you want to predict? Be specific..."
                  className="w-full h-24 px-4 py-3 bg-gray-950 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 resize-none transition-all"
                />
                
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="text-xs text-gray-500 mr-2">Try:</span>
                  {exampleQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => setQuery(q)}
                      className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-blue-500/20 text-gray-400 hover:text-blue-300 rounded-full transition-all duration-200 border border-transparent hover:border-blue-500/30"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <button
                data-testid="extract-graph-button"
                onClick={handleSubmit}
                disabled={!file || !query.trim() || loading}
                className="w-full mt-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold rounded-xl flex items-center justify-center gap-3 transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 disabled:shadow-none"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Analyzing Document...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    <span>Extract Knowledge Graph</span>
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </>
          ) : (
            /* Live Intelligence Mode Content */
            <>
              <div className="space-y-6">
                {/* Topic Input */}
                <div>
                  <label className="block text-sm font-semibold text-white mb-2 flex items-center gap-2">
                    <Globe className="w-4 h-4 text-green-400" />
                    Topic to Track
                  </label>
                  <input
                    data-testid="topic-input"
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g., Bitcoin price, Tesla earnings, Fed interest rate decision..."
                    className="w-full px-4 py-3 bg-gray-950 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20 transition-all"
                  />
                  <div className="mt-3 flex flex-wrap gap-2">
                    <span className="text-xs text-gray-500 mr-2">Popular:</span>
                    {exampleTopics.map((t, i) => (
                      <button
                        key={i}
                        onClick={() => setTopic(t)}
                        className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-green-500/20 text-gray-400 hover:text-green-300 rounded-full transition-all duration-200 border border-transparent hover:border-green-500/30"
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Prediction Horizon */}
                <div>
                  <label className="block text-sm font-semibold text-white mb-2 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-green-400" />
                    Prediction Horizon
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {PREDICTION_HORIZONS.map((h) => (
                      <button
                        key={h}
                        onClick={() => setHorizon(h)}
                        className={`px-3 py-2 rounded-lg text-sm transition-all ${
                          horizon === h
                            ? "bg-green-600 text-white"
                            : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
                        }`}
                      >
                        {h}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Custom Prediction Question (Optional) */}
                <div>
                  <label className="block text-sm font-semibold text-white mb-2 flex items-center gap-2">
                    🎯 Custom Question <span className="text-gray-500 font-normal">(optional)</span>
                  </label>
                  <input
                    data-testid="live-query-input"
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Leave blank for auto-generated question..."
                    className="w-full px-4 py-3 bg-gray-950 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20 transition-all"
                  />
                </div>

                {/* What Live Mode Does */}
                <div className="bg-green-500/5 border border-green-500/20 rounded-xl p-4">
                  <h4 className="text-sm font-semibold text-green-400 mb-2 flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    What Live Intelligence Does
                  </h4>
                  <ul className="text-xs text-gray-400 space-y-1">
                    <li className="flex items-center gap-2"><Wifi className="w-3 h-3 text-green-400" /> Fetches latest news and data from the web</li>
                    <li className="flex items-center gap-2"><Users className="w-3 h-3 text-green-400" /> Creates topic-specialized agent personas</li>
                    <li className="flex items-center gap-2"><TrendingUp className="w-3 h-3 text-green-400" /> Generates intelligence brief with key metrics</li>
                  </ul>
                </div>
              </div>

              {/* Submit Button */}
              <button
                data-testid="fetch-live-button"
                onClick={handleSubmit}
                disabled={!topic.trim() || loading}
                className="w-full mt-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold rounded-xl flex items-center justify-center gap-3 transition-all duration-300 shadow-lg shadow-green-500/25 hover:shadow-green-500/40 disabled:shadow-none"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Fetching Live Data...</span>
                  </>
                ) : (
                  <>
                    <Radio className="w-5 h-5" />
                    <span>Fetch & Analyze</span>
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Features */}
      <div className="grid grid-cols-3 gap-4 mt-8">
        {[
          { icon: "🧠", title: "AI Analysis", desc: "Claude extracts entities & relationships" },
          { icon: "👥", title: "Agent Swarm", desc: "10-50 AI agents debate the topic" },
          { icon: "📊", title: "Predictions", desc: "Confidence scores & faction analysis" }
        ].map((feature, i) => (
          <div key={i} className="text-center p-4 bg-gray-900/50 border border-gray-800 rounded-xl hover:border-gray-700 transition-colors">
            <span className="text-2xl mb-2 block">{feature.icon}</span>
            <h4 className="text-sm font-semibold text-white mb-1">{feature.title}</h4>
            <p className="text-xs text-gray-500">{feature.desc}</p>
          </div>
        ))}
      </div>

      <div className="mt-6">
        <SystemDashboard logs={logs} />
      </div>
    </div>
  );
};

// Agent Card Component
const AgentCard = ({ agent, showPreview = false }) => (
  <div className="bg-gray-900 border border-gray-800 rounded-lg p-3 hover:border-gray-600 transition-colors animate-fade-in">
    <div className="flex items-start gap-3">
      <span className="text-3xl">{agent.avatar_emoji}</span>
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-bold text-white truncate">{agent.name}</h4>
        <p className="text-[11px] text-gray-400 truncate">{agent.occupation}</p>
        <div className="flex items-center gap-2 mt-1.5">
          <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${PERSONALITY_COLORS[agent.personality_type] || "badge-neutral"}`}>
            {agent.personality_type}
          </span>
          <span className="text-[10px] text-gray-500 flex items-center gap-0.5">
            <Target className="w-2.5 h-2.5" />
            {agent.influence_level}/10
          </span>
        </div>
        {showPreview && agent.initial_stance && (
          <p className="text-[11px] text-gray-400 mt-2 line-clamp-2 italic">
            "{agent.initial_stance}"
          </p>
        )}
      </div>
    </div>
  </div>
);

// Agent Step Component with Preview
const AgentStep = ({ sessionId, graph, onComplete }) => {
  const [numAgents, setNumAgents] = useState(20);
  const [loading, setLoading] = useState(false);
  const [agents, setAgents] = useState(null);
  const [error, setError] = useState(null);
  const [logs, setLogs] = useState([]);

  const addLog = (message, type = "info") => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    setLogs(prev => [...prev.slice(-20), { time, message, type }]);
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    addLog(`Generating ${numAgents} agents...`);
    try {
      // Kick off background generation
      await axios.post(`${API}/sessions/${sessionId}/generate-agents`, {
        num_agents: numAgents,
      }, { timeout: 15000 });
      addLog("Agent generation started, please wait...");
      
      // Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await axios.get(`${API}/sessions/${sessionId}/agent-status`, { timeout: 10000 });
          const data = statusRes.data;
          
          if (data.status === "completed") {
            clearInterval(pollInterval);
            addLog(`Successfully created ${data.agents.length} agents`, "success");
            setAgents(data.agents);
            setLoading(false);
          } else if (data.status === "failed") {
            clearInterval(pollInterval);
            const errMsg = data.error || "Agent generation failed";
            addLog(`Error: ${errMsg}`, "error");
            setError(errMsg);
            setLoading(false);
          }
        } catch (pollErr) {
          // Polling error is transient, keep trying
          addLog("Checking status...", "info");
        }
      }, 3000);
      
      // Safety timeout after 3 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (!agents) {
          setError("Agent generation is taking too long. Please try again with fewer agents.");
          setLoading(false);
        }
      }, 180000);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || "Failed to generate agents";
      setError(errorMsg);
      addLog(`Error: ${errorMsg}`, "error");
      setLoading(false);
    }
  };

  const personalityCounts = agents?.reduce((acc, agent) => {
    acc[agent.personality_type] = (acc[agent.personality_type] || 0) + 1;
    return acc;
  }, {});

  if (agents) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in">
        {/* Left: Knowledge Graph */}
        <div className="h-[600px]">
          <KnowledgeGraph graph={graph} onRefresh={() => {}} />
        </div>

        {/* Right: Agent Grid */}
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">{agents.length} Agents Generated</h3>
              <span className="text-xs text-gray-400">Ready to simulate</span>
            </div>
            
            {/* Personality Distribution */}
            <div className="flex flex-wrap gap-1.5 mb-4">
              {Object.entries(personalityCounts || {}).map(([type, count]) => (
                <span key={type} className={`text-[10px] px-2 py-0.5 rounded-full border ${PERSONALITY_COLORS[type] || "badge-neutral"}`}>
                  {type}: {count}
                </span>
              ))}
            </div>

            {/* Agent Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[400px] overflow-y-auto pr-2">
              {agents.slice(0, 8).map((agent) => (
                <AgentCard key={agent.id} agent={agent} showPreview={true} />
              ))}
            </div>
            {agents.length > 8 && (
              <p className="text-center text-xs text-gray-500 mt-3">
                +{agents.length - 8} more agents
              </p>
            )}
          </div>

          <SystemDashboard logs={logs} />

          <button
            data-testid="start-simulation-button"
            onClick={() => onComplete(agents)}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            Start Simulation →
            <Play className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left: Knowledge Graph */}
      <div className="h-[600px]">
        <KnowledgeGraph graph={graph} onRefresh={() => {}} />
      </div>

      {/* Right: Agent Config */}
      <div className="space-y-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-lg font-bold text-white mb-4">Generate AI Agents</h3>
          
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="flex items-center gap-2 text-red-400 text-sm mb-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
              <button
                data-testid="retry-agents-button"
                onClick={handleGenerate}
                className="text-xs px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Context Summary */}
          <div className="bg-gray-950 rounded-lg p-3 mb-4 border border-gray-800">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">World Context</p>
            <p className="text-sm text-gray-300">{graph?.summary}</p>
          </div>

          {/* Agent Count Slider */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-300">Number of Agents</label>
              <span className="text-xl font-bold text-blue-400 mono">{numAgents}</span>
            </div>
            <input
              data-testid="agent-count-slider"
              type="range"
              min="10"
              max="300"
              value={numAgents}
              onChange={(e) => setNumAgents(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
            <div className="flex justify-between text-[10px] text-gray-500 mt-1">
              <span>10</span>
              <span>100</span>
              <span>200</span>
              <span>300</span>
            </div>
          </div>

          {/* Estimate */}
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 mb-4">
            <div className="flex items-center gap-2 text-amber-400 text-xs">
              <Settings className="w-3.5 h-3.5" />
              <span>Estimated time: ~{Math.ceil(numAgents / 10) * 15} seconds</span>
            </div>
          </div>

          <button
            data-testid="generate-agents-button"
            onClick={handleGenerate}
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-500/20 disabled:shadow-none"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating {numAgents} Agents...
              </>
            ) : (
              <>
                <Users className="w-4 h-4" />
                Generate Agents
              </>
            )}
          </button>

          {/* Loading Skeleton Preview */}
          {loading && (
            <div className="mt-4 space-y-3 animate-fade-in">
              <p className="text-xs text-gray-500 text-center">Creating agent personas...</p>
              <SkeletonGrid count={4} />
            </div>
          )}
        </div>

        <SystemDashboard logs={logs} />
      </div>
    </div>
  );
};

// Post Card Component
const PostCard = ({ post, isReply }) => (
  <div
    className={`p-3 border border-gray-800 rounded-lg bg-gray-950/50 hover:bg-gray-800/50 transition-colors animate-slide-up ${
      isReply ? "ml-4 border-l-2 border-l-blue-500" : ""
    } ${post.platform === "Reddit" ? "border-l-2 border-l-orange-500" : ""}`}
  >
    <div className="flex items-start gap-2">
      <span className="text-xl">{post.agent_emoji}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5 flex-wrap">
          <span className="font-semibold text-white text-xs">{post.agent_name}</span>
          <span className="text-[10px] text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">R{post.round}</span>
          {post.is_hub_post && (
            <span className="text-[10px] bg-purple-500/20 text-purple-400 border border-purple-500/30 px-1.5 py-0.5 rounded-full">HUB</span>
          )}
          {post.belief_position != null && (
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
              post.belief_position > 0.15 ? 'bg-green-500/15 text-green-400' :
              post.belief_position < -0.15 ? 'bg-red-500/15 text-red-400' :
              'bg-gray-500/15 text-gray-400'
            }`}>
              {post.belief_position > 0.15 ? '+ support' : post.belief_position < -0.15 ? '- oppose' : '~ undecided'}
            </span>
          )}
          {isReply && (
            <span className="text-[10px] text-blue-400">&#8617; {post.reply_to}</span>
          )}
        </div>
        <p className="text-gray-300 text-xs">{post.content}</p>
      </div>
    </div>
  </div>
);

// Simulation View Component
const SimulationView = ({ sessionId, agents, onComplete }) => {
  const [numRounds, setNumRounds] = useState(5);
  const [simulating, setSimulating] = useState(false);
  const [status, setStatus] = useState(null);
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState(null);
  const [logs, setLogs] = useState([]);
  const [simMeta, setSimMeta] = useState(null);
  const twitterFeedRef = useRef(null);
  const redditFeedRef = useRef(null);

  const addLog = (message, type = "info") => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    setLogs(prev => [...prev.slice(-30), { time, message, type }]);
  };

  const startSimulation = async () => {
    setSimulating(true);
    setError(null);
    addLog(`Starting simulation with ${numRounds} rounds...`);
    addLog(`${agents?.length || 0} agents participating`);
    try {
      await axios.post(`${API}/sessions/${sessionId}/simulate`, { num_rounds: numRounds });
      addLog("Simulation started", "success");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start simulation");
      addLog("Failed to start simulation", "error");
      setSimulating(false);
    }
  };

  useEffect(() => {
    if (!simulating) return;

    const interval = setInterval(async () => {
      try {
        const [statusRes, postsRes] = await Promise.all([
          axios.get(`${API}/sessions/${sessionId}/simulation-status`),
          axios.get(`${API}/sessions/${sessionId}/posts`),
        ]);
        setStatus(statusRes.data);
        
        // Extract sim meta for new AI enhancements
        if (statusRes.data.belief_summary || statusRes.data.emotional_summary) {
          setSimMeta({
            beliefSummary: statusRes.data.belief_summary,
            emotionalSummary: statusRes.data.emotional_summary,
            networkStats: statusRes.data.network_stats,
            roundNarratives: statusRes.data.round_narratives || [],
          });
        }
        
        if (postsRes.data.posts.length > posts.length) {
          const newPosts = postsRes.data.posts.slice(posts.length);
          newPosts.forEach(p => {
            addLog(`[${p.platform}] ${p.agent_name}: ${p.content.slice(0, 40)}...`);
          });
        }
        setPosts(postsRes.data.posts);

        if (statusRes.data.status === "simulation_done") {
          addLog("Simulation complete!", "success");
          clearInterval(interval);
        } else if (statusRes.data.status === "error") {
          setError("Simulation encountered an error");
          addLog("Simulation error", "error");
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [simulating, sessionId, posts.length]);

  useEffect(() => {
    if (twitterFeedRef.current) {
      twitterFeedRef.current.scrollTop = twitterFeedRef.current.scrollHeight;
    }
    if (redditFeedRef.current) {
      redditFeedRef.current.scrollTop = redditFeedRef.current.scrollHeight;
    }
  }, [posts]);

  const twitterPosts = posts.filter((p) => p.platform === "Twitter");
  const redditPosts = posts.filter((p) => p.platform === "Reddit");
  const isDone = status?.status === "simulation_done";

  if (!simulating && posts.length === 0) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Agent Preview */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h3 className="text-lg font-bold text-white mb-4">Participating Agents ({agents?.length || 0})</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 max-h-[450px] overflow-y-auto pr-2">
              {agents?.map((agent) => (
                <div key={agent.id} className="bg-gray-950 border border-gray-800 rounded-lg p-2 text-center">
                  <span className="text-2xl">{agent.avatar_emoji}</span>
                  <p className="text-xs text-white font-medium truncate mt-1">{agent.name}</p>
                  <p className="text-[10px] text-gray-500 truncate">{agent.occupation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Simulation Config */}
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-lg font-bold text-white mb-1">Simulation Settings</h3>
            <p className="text-xs text-gray-400 mb-4">Configure rounds and start</p>

            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400 text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-300">Number of Rounds</label>
                <span className="text-xl font-bold text-blue-400 mono">{numRounds}</span>
              </div>
              <input
                data-testid="rounds-slider"
                type="range"
                min="3"
                max="15"
                value={numRounds}
                onChange={(e) => setNumRounds(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-gray-500 mt-1">
                <span>3</span>
                <span>9</span>
                <span>15</span>
              </div>
            </div>

            <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 mb-4">
              <p className="text-amber-400 text-xs">
                Estimated time: ~{numRounds * 30} seconds
              </p>
            </div>

            <button
              data-testid="run-simulation-button"
              onClick={startSimulation}
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
            >
              <Play className="w-4 h-4" />
              Start Simulation
            </button>
          </div>

          <SystemDashboard logs={logs} />
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in space-y-4">
      {/* Progress Bar */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">
            {isDone ? "Simulation Complete" : `Round ${status?.current_round || 0} of ${status?.total_rounds || numRounds}`}
          </span>
          <span className="text-sm text-blue-400 mono font-bold">{posts.length} posts</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-emerald-500 transition-all duration-500"
            style={{ width: `${((status?.current_round || 0) / (status?.total_rounds || numRounds)) * 100}%` }}
          />
        </div>
      </div>

      {/* AI Enhancement Panels */}
      {simMeta && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {/* Emotional Temperature */}
          <div className="bg-gray-900/50 rounded-xl p-3 border border-gray-800">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Crowd Emotion</p>
            <EmotionalTemperatureGauge data={simMeta.emotionalSummary} />
          </div>
          {/* Belief Distribution */}
          {simMeta.beliefSummary && (
            <div className="bg-gray-900/50 rounded-xl p-3 border border-gray-800">
              <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Belief Distribution</p>
              <div className="flex gap-2 text-xs">
                <span className="bg-green-500/15 text-green-400 px-2 py-1 rounded">{simMeta.beliefSummary.support}% support</span>
                <span className="bg-red-500/15 text-red-400 px-2 py-1 rounded">{simMeta.beliefSummary.opposition}% oppose</span>
                <span className="bg-gray-500/15 text-gray-400 px-2 py-1 rounded">{simMeta.beliefSummary.undecided}% undecided</span>
              </div>
            </div>
          )}
          {/* Network Stats */}
          {simMeta.networkStats && (
            <div className="bg-gray-900/50 rounded-xl p-3 border border-gray-800">
              <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Network</p>
              <div className="flex gap-2 text-xs">
                <span className="bg-purple-500/15 text-purple-400 px-2 py-1 rounded">{simMeta.networkStats.hub_count} hubs</span>
                <span className="bg-gray-500/15 text-gray-400 px-2 py-1 rounded">{simMeta.networkStats.peripheral_count} peripheral</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sentiment Chart */}
      {posts.length > 5 && <SentimentChart posts={posts} />}

      {/* Dual Feed Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Twitter Feed */}
        <div className="flex flex-col h-[500px] border border-gray-800 rounded-xl bg-gray-900 overflow-hidden">
          <div className="px-3 py-2 border-b border-gray-800 flex items-center justify-between bg-gray-950">
            <div className="flex items-center gap-2">
              <Twitter className="w-4 h-4 text-blue-400" />
              <span className="font-semibold text-white text-sm">Twitter Feed</span>
            </div>
            <span className="text-[10px] text-gray-500">{twitterPosts.length} posts</span>
          </div>
          <div ref={twitterFeedRef} className="flex-1 overflow-y-auto p-3 space-y-2">
            {twitterPosts.map((post, i) => (
              <PostCard key={i} post={post} isReply={post.post_type === "reply"} />
            ))}
            {!isDone && twitterPosts.length === 0 && (
              <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Waiting for posts...
              </div>
            )}
          </div>
        </div>

        {/* Reddit Feed */}
        <div className="flex flex-col h-[500px] border border-gray-800 rounded-xl bg-gray-900 overflow-hidden">
          <div className="px-3 py-2 border-b border-gray-800 flex items-center justify-between bg-gray-950">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-orange-500 flex items-center justify-center text-white text-[10px] font-bold">R</div>
              <span className="font-semibold text-white text-sm">Reddit Feed</span>
            </div>
            <span className="text-[10px] text-gray-500">{redditPosts.length} posts</span>
          </div>
          <div ref={redditFeedRef} className="flex-1 overflow-y-auto p-3 space-y-2">
            {redditPosts.map((post, i) => (
              <PostCard key={i} post={post} isReply={post.post_type === "reply"} />
            ))}
            {!isDone && redditPosts.length === 0 && (
              <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Waiting for posts...
              </div>
            )}
          </div>
        </div>
      </div>

      <SystemDashboard logs={logs} />

      {isDone && (
        <button
          data-testid="generate-report-button"
          onClick={() => onComplete(posts)}
          className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
        >
          Generate Report →
          <BarChart3 className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

// Confidence Gauge Component
const ConfidenceGauge = ({ score, confidence }) => {
  const percentage = Math.round(score * 100);
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (score * circumference);
  const color = confidence === "High" ? "#10b981" : confidence === "Medium" ? "#f59e0b" : "#ef4444";
  
  return (
    <div className="relative w-28 h-28">
      <svg className="w-full h-full -rotate-90">
        <circle
          cx="56"
          cy="56"
          r="40"
          fill="none"
          stroke="#1f2937"
          strokeWidth="8"
        />
        <circle
          cx="56"
          cy="56"
          r="40"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white mono">{percentage}%</span>
        <span className="text-[10px] text-gray-400">{confidence}</span>
      </div>
    </div>
  );
};

// Report View Component
const ReportView = ({ sessionId, posts, onComplete }) => {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [sessionMeta, setSessionMeta] = useState(null);

  useEffect(() => {
    axios.get(`${API}/sessions/${sessionId}/simulation-status`)
      .then(res => setSessionMeta(res.data))
      .catch(() => {});
  }, [sessionId]);

  const generateReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API}/sessions/${sessionId}/generate-report`);
      setReport(response.data.report);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate report");
    } finally {
      setLoading(false);
    }
  };

  if (!report && !loading) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <div className="w-20 h-20 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-4">
          <BarChart3 className="w-10 h-10 text-blue-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Generate Prediction Report</h2>
        <p className="text-gray-400 text-sm mb-6">
          Analyze {posts?.length || 0} posts to produce insights
        </p>
        
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400 text-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          data-testid="analyze-report-button"
          onClick={generateReport}
          className="py-3 px-6 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 mx-auto transition-colors"
        >
          <BarChart3 className="w-4 h-4" />
          Generate Report
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
        {/* Loading Header */}
        <div className="text-center py-8">
          <div className="relative inline-block">
            <div className="w-20 h-20 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 animate-spin mx-auto" style={{ animationDuration: '3s' }}>
              <div className="absolute inset-2 bg-gray-950 rounded-full" />
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl">🧠</span>
            </div>
          </div>
          <h2 className="text-xl font-bold text-white mt-6 mb-2">ReportAgent Analyzing...</h2>
          <p className="text-gray-400 text-sm">Processing simulation data and generating insights</p>
        </div>

        {/* Skeleton Report Preview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-4">
            <SkeletonCard />
            <SkeletonCard />
          </div>
          <div className="space-y-4">
            <SkeletonCard />
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-3">
              <Skeleton className="h-5 w-1/3" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-4/5" />
              <Skeleton className="h-3 w-3/5" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in space-y-4">
      {/* Header with Confidence */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex-1">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Predicted Outcome</p>
            <p className="text-xl font-bold text-white mb-2">{report.prediction?.outcome}</p>
            <p className="text-sm text-gray-400">Timeframe: {report.prediction?.timeframe}</p>
          </div>
          <ConfidenceGauge 
            score={report.prediction?.confidence_score || 0.5}
            confidence={report.prediction?.confidence}
          />
        </div>
        {/* Simulation Quality Badge */}
        {report.quality_score != null && (
          <div data-testid="quality-score-badge" className={`mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${
            report.quality_score >= 8 ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400' :
            report.quality_score >= 6 ? 'bg-blue-500/15 border-blue-500/40 text-blue-400' :
            report.quality_score >= 4 ? 'bg-yellow-500/15 border-yellow-500/40 text-yellow-400' :
            'bg-red-500/15 border-red-500/40 text-red-400'
          }`}>
            <Shield className="w-3.5 h-3.5" />
            Simulation Quality: {
              report.quality_score >= 8 ? 'Excellent' :
              report.quality_score >= 6 ? 'Good' :
              report.quality_score >= 4 ? 'Fair' : 'Low'
            } ({report.quality_score}/10)
            {report.overconfident && <span className="text-yellow-400 ml-1">(overconfident)</span>}
          </div>
        )}
      </div>

      {/* Simulation Story Arc & AI Insights */}
      {sessionMeta && (sessionMeta.round_narratives?.length > 0 || sessionMeta.emotional_summary) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          {/* Story Arc */}
          {sessionMeta.round_narratives?.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <h3 data-testid="story-arc" className="text-sm font-bold text-white mb-2">Simulation Story Arc</h3>
              <div className="space-y-1.5">
                {sessionMeta.round_narratives.map((n, i) => (
                  <p key={i} className="text-xs text-gray-400 leading-relaxed">
                    <span className="text-blue-400 font-medium">{n.startsWith("R") || n.startsWith("BREAKING") ? "" : `Round ${i+1}: `}</span>{n}
                  </p>
                ))}
              </div>
            </div>
          )}
          {/* Emotional Temperature & Belief Summary */}
          <div className="space-y-3">
            {sessionMeta.emotional_summary && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <h3 className="text-sm font-bold text-white mb-2">Final Crowd Emotion</h3>
                <EmotionalTemperatureGauge data={sessionMeta.emotional_summary} />
              </div>
            )}
            {sessionMeta.belief_summary && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <h3 className="text-sm font-bold text-white mb-2">Final Belief Distribution</h3>
                <div className="flex gap-2 text-xs flex-wrap">
                  <span className="bg-green-500/15 text-green-400 px-2 py-1 rounded">{sessionMeta.belief_summary.support}% support</span>
                  <span className="bg-red-500/15 text-red-400 px-2 py-1 rounded">{sessionMeta.belief_summary.opposition}% oppose</span>
                  <span className="bg-gray-500/15 text-gray-400 px-2 py-1 rounded">{sessionMeta.belief_summary.undecided}% undecided</span>
                  {sessionMeta.belief_summary.polarisation != null && (
                    <span className="bg-yellow-500/15 text-yellow-400 px-2 py-1 rounded">Polarisation: {sessionMeta.belief_summary.polarisation?.toFixed(2)}</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sentiment Chart */}
      {posts?.length > 5 && <SentimentChart posts={posts} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-4">
          {/* Executive Summary */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-bold text-white mb-2">Executive Summary</h3>
            <p className="text-sm text-gray-300 leading-relaxed">{report.executive_summary}</p>
          </div>

          {/* Opinion Landscape */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-bold text-white mb-3">Opinion Landscape</h3>
            
            <div className="flex h-3 rounded-full overflow-hidden mb-2">
              <div className="bg-emerald-500" style={{ width: `${report.opinion_landscape?.support_percentage || 0}%` }} />
              <div className="bg-red-500" style={{ width: `${report.opinion_landscape?.opposition_percentage || 0}%` }} />
              <div className="bg-gray-600" style={{ width: `${report.opinion_landscape?.undecided_percentage || 0}%` }} />
            </div>
            <div className="flex justify-between text-[10px]">
              <span className="text-emerald-400">Support: {report.opinion_landscape?.support_percentage}%</span>
              <span className="text-red-400">Oppose: {report.opinion_landscape?.opposition_percentage}%</span>
              <span className="text-gray-400">Undecided: {report.opinion_landscape?.undecided_percentage}%</span>
            </div>
          </div>

          {/* Key Factions */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-bold text-white mb-3">Key Factions</h3>
            <div className="space-y-2">
              {report.opinion_landscape?.key_factions?.map((faction, i) => (
                <div key={i} className="p-2.5 bg-gray-950 rounded-lg border border-gray-800">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-white text-sm">{faction.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      faction.size === "Large" ? "bg-blue-500/20 text-blue-400" :
                      faction.size === "Medium" ? "bg-amber-500/20 text-amber-400" :
                      "bg-gray-500/20 text-gray-400"
                    }`}>
                      {faction.size}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">{faction.stance}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-4">
          {/* Risk Factors */}
          {report.risk_factors?.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                Risk Factors
              </h3>
              <div className="space-y-2">
                {report.risk_factors.map((risk, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 rounded bg-red-500/5 border border-red-500/10">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 ${
                      risk.likelihood === "High" ? "bg-red-500/20 text-red-400" :
                      risk.likelihood === "Medium" ? "bg-amber-500/20 text-amber-400" :
                      "bg-gray-500/20 text-gray-400"
                    }`}>
                      {risk.likelihood}
                    </span>
                    <div>
                      <p className="text-sm text-white font-medium">{risk.factor}</p>
                      <p className="text-xs text-gray-400">{risk.impact}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Turning Points */}
          {report.key_turning_points?.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-bold text-white mb-3">Key Turning Points</h3>
              <div className="space-y-2">
                {report.key_turning_points.map((point, i) => (
                  <div key={i} className="flex gap-2">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold text-[10px]">
                      R{point.round}
                    </div>
                    <div>
                      <p className="text-sm text-white">{point.description}</p>
                      <p className="text-xs text-gray-400">{point.impact}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Agent Highlights */}
          {report.agent_highlights?.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-bold text-white mb-3">Agent Highlights</h3>
              <div className="space-y-2">
                {report.agent_highlights.slice(0, 3).map((highlight, i) => (
                  <div key={i} className="p-2.5 bg-gray-950 rounded-lg border border-gray-800">
                    <p className="font-medium text-white text-sm">{highlight.agent_name}</p>
                    <p className="text-xs text-gray-400 mb-1">{highlight.role_in_simulation}</p>
                    <p className="text-xs text-blue-300 italic">"{highlight.notable_quote?.slice(0, 80)}..."</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          data-testid="download-pdf-button"
          onClick={() => window.open(`${API}/sessions/${sessionId}/report/pdf`, '_blank')}
          className="flex-1 py-3 bg-gray-800 hover:bg-gray-700 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors border border-gray-700"
        >
          <Download className="w-4 h-4" />
          Download PDF
        </button>
        
        <button
          data-testid="interact-with-agents-button"
          onClick={() => onComplete(report)}
          className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
        >
          💬 Interact with Agents
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

// Chat Panel Component
const ChatPanel = ({ sessionId, agents, report }) => {
  const [selectedTarget, setSelectedTarget] = useState({ type: "report", id: "report_agent", name: "ReportAgent" });
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await axios.get(
          `${API}/sessions/${sessionId}/chat-history?target_type=${selectedTarget.type}&target_id=${selectedTarget.id}`
        );
        setMessages(response.data.history || []);
      } catch (err) {
        setMessages([]);
      }
    };
    loadHistory();
  }, [sessionId, selectedTarget]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    
    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const response = await axios.post(`${API}/sessions/${sessionId}/chat`, {
        target_type: selectedTarget.type,
        target_id: selectedTarget.id,
        message: userMessage,
      });
      setMessages(prev => [...prev, { role: "assistant", content: response.data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = selectedTarget.type === "report"
    ? ["What's the most important finding?", "What are the biggest risks?", "How confident should I be?"]
    : ["What's your take on this?", "Why do you feel that way?", "What would change your mind?"];

  return (
    <div className="flex h-[600px] border border-gray-800 rounded-xl overflow-hidden bg-gray-900">
      {/* Sidebar */}
      <div className="w-56 border-r border-gray-800 bg-gray-950 overflow-y-auto hidden md:block">
        <div className="p-3 border-b border-gray-800">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Chat Targets</h3>
        </div>
        
        <button
          data-testid="chat-target-report-agent"
          onClick={() => setSelectedTarget({ type: "report", id: "report_agent", name: "ReportAgent" })}
          className={`w-full p-3 flex items-center gap-2 border-b border-gray-800 transition-colors ${
            selectedTarget.id === "report_agent" ? "bg-blue-500/10 border-l-2 border-l-blue-500" : "hover:bg-gray-900"
          }`}
        >
          <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-lg">
            🧠
          </div>
          <div className="text-left">
            <p className="font-semibold text-white text-xs">ReportAgent</p>
            <p className="text-[10px] text-gray-500">Analysis Expert</p>
          </div>
        </button>

        <div className="p-2">
          <p className="text-[10px] text-gray-500 px-2 py-1">Agents ({agents?.length || 0})</p>
        </div>
        {agents?.slice(0, 10).map((agent) => (
          <button
            key={agent.id}
            data-testid={`chat-target-${agent.id}`}
            onClick={() => setSelectedTarget({ type: "agent", id: agent.id, name: agent.name, agent })}
            className={`w-full p-2 flex items-center gap-2 border-b border-gray-800/50 transition-colors ${
              selectedTarget.id === agent.id ? "bg-blue-500/10 border-l-2 border-l-blue-500" : "hover:bg-gray-900"
            }`}
          >
            <span className="text-xl">{agent.avatar_emoji}</span>
            <div className="text-left min-w-0">
              <p className="font-medium text-white text-xs truncate">{agent.name}</p>
              <p className="text-[10px] text-gray-500 truncate">{agent.occupation}</p>
            </div>
          </button>
        ))}
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="px-4 py-3 border-b border-gray-800 bg-gray-950 flex items-center gap-2">
          <span className="text-xl">
            {selectedTarget.type === "report" ? "🧠" : selectedTarget.agent?.avatar_emoji}
          </span>
          <div>
            <h3 className="font-semibold text-white text-sm">{selectedTarget.name}</h3>
            <p className="text-[10px] text-gray-500">
              {selectedTarget.type === "report" ? "Analysis Expert" : selectedTarget.agent?.occupation}
            </p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-6">
              <p className="text-sm mb-3">Start a conversation</p>
              <div className="flex flex-wrap justify-center gap-2">
                {quickPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(prompt)}
                    className="text-xs px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-full transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}
            >
              <div
                className={`max-w-[80%] px-3 py-2 rounded-2xl text-sm ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-tr-sm"
                    : "bg-gray-800 text-gray-200 rounded-tl-sm"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 text-gray-200 px-3 py-2 rounded-2xl rounded-tl-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="p-3 border-t border-gray-800 bg-gray-950">
          <div className="flex gap-2">
            <input
              data-testid="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder={`Message ${selectedTarget.name}...`}
              className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
            <button
              data-testid="send-message-button"
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [sessionId, setSessionId] = useState(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [graph, setGraph] = useState(null);
  const [agents, setAgents] = useState(null);
  const [posts, setPosts] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const createNewSession = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/sessions`);
      setSessionId(response.data.session_id);
      // Reset all state
      setCurrentStep(1);
      setCompletedSteps([]);
      setGraph(null);
      setAgents(null);
      setPosts(null);
      setReport(null);
      setError(null);
    } catch (err) {
      setError("Failed to create session. Please refresh the page.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    createNewSession();
  }, []);

  const handleNewSimulation = () => {
    if (window.confirm("Start a new simulation? All current progress will be lost.")) {
      createNewSession();
    }
  };

  const handleStepComplete = (step, data) => {
    setCompletedSteps((prev) => [...new Set([...prev, step])]);
    
    switch (step) {
      case 1:
        setGraph(data);
        setCurrentStep(2);
        break;
      case 2:
        setAgents(data);
        setCurrentStep(3);
        break;
      case 3:
        setPosts(data);
        setCurrentStep(4);
        break;
      case 4:
        setReport(data);
        setCurrentStep(5);
        break;
      default:
        break;
    }
  };

  const handleStepClick = (stepId) => {
    if (completedSteps.includes(stepId) || stepId <= Math.max(...completedSteps, 1)) {
      setCurrentStep(stepId);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 relative overflow-hidden">
        <ParticleBackground />
        <div className="relative z-10 flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="relative">
              <div className="w-20 h-20 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 animate-spin mx-auto mb-6" style={{ animationDuration: '2s' }}>
                <div className="absolute inset-2 bg-gray-950 rounded-full" />
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-3xl">🐟</span>
              </div>
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Initializing SwarmSim</h2>
            <p className="text-gray-400 text-sm">Preparing your prediction engine...</p>
            <div className="mt-6 flex justify-center gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 relative overflow-hidden">
        <ParticleBackground />
        <div className="relative z-10 flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-10 h-10 text-red-400" />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Connection Error</h2>
            <p className="text-gray-400 mb-4">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 relative overflow-hidden">
      {/* Particle Background */}
      <ParticleBackground />
      
      {/* Main Content */}
      <div className="relative z-10">
        <Header onNewSimulation={handleNewSimulation} hasSession={!!sessionId} />
        
        <main className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <StepIndicator
            currentStep={currentStep}
            completedSteps={completedSteps}
            onStepClick={handleStepClick}
          />

          <div className="mt-6">
            {currentStep === 1 && (
              <UploadStep
                sessionId={sessionId}
                onComplete={(data) => handleStepComplete(1, data)}
              />
            )}
            
            {currentStep === 2 && (
              <AgentStep
                sessionId={sessionId}
                graph={graph}
                onComplete={(data) => handleStepComplete(2, data)}
              />
            )}
            
            {currentStep === 3 && (
              <SimulationView
                sessionId={sessionId}
                agents={agents}
                onComplete={(data) => handleStepComplete(3, data)}
              />
            )}
            
            {currentStep === 4 && (
              <ReportView
                sessionId={sessionId}
                posts={posts}
                onComplete={(data) => handleStepComplete(4, data)}
              />
            )}
          
          {currentStep === 5 && (
            <ChatPanel
              sessionId={sessionId}
              agents={agents}
              report={report}
            />
          )}
        </div>
      </main>
      </div>
    </div>
  );
}

export default App;
