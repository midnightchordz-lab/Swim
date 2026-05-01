import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import axios from "axios";
import ForceGraph2D from "react-force-graph-2d";
import {
  Upload, FileText, Users, Play, BarChart3, MessageSquare,
  Loader2, ArrowRight, Send, AlertCircle, CheckCircle,
  Twitter, ChevronRight, Zap, Target, TrendingUp, AlertTriangle,
  Download, RefreshCw, Eye, EyeOff, Settings, Terminal,
  Globe, Radio, Clock, Wifi, Shield
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip as ReTooltip,
  ResponsiveContainer, CartesianGrid,
} from "recharts";
import PredictionQualityPanel from "./components/PredictionQualityPanel";
import ProgressStatusCard from "./components/ProgressStatusCard";
import SimulationFeed from "./components/SimulationFeed";
import LandingOnboarding from "./components/LandingOnboarding";
import ScenarioTemplates from "./components/ScenarioTemplates";
import SimulationReplayTimeline from "./components/SimulationReplayTimeline";
import GodViewInjectionPanel from "./components/GodViewInjectionPanel";
import EnsembleForecastPanel from "./components/EnsembleForecastPanel";
import EvidenceLedgerPanel from "./components/EvidenceLedgerPanel";
import AuthLandingGate from "./components/AuthLandingGate";
import ParticleBackground from "./components/ParticleBackground";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const setAuthToken = (token) => {
  if (token) {
    axios.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common.Authorization;
  }
};

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
  <div className={`animate-pulse bg-sw-bg3 rounded ${className}`} />
);

// Skeleton Card Component
const SkeletonCard = () => (
  <div className="bg-panel border border-sw rounded-xl p-6 space-y-4">
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
      <div key={i} className="bg-panel border border-sw rounded-lg p-4 space-y-3">
        <Skeleton className="w-10 h-10 rounded-full mx-auto" />
        <Skeleton className="h-4 w-3/4 mx-auto" />
        <Skeleton className="h-3 w-1/2 mx-auto" />
      </div>
    ))}
  </div>
);

// Entity type colors
const ENTITY_COLORS = {
  person: "#f97316",
  Person: "#f97316",
  organization: "#3b82f6",
  Organization: "#3b82f6",
  faction: "#a855f7",
  concept: "#22c55e",
  Concept: "#22c55e",
  event: "#ef4444",
  Event: "#ef4444",
  Country: "#06b6d4",
  Company: "#8b5cf6",
  Policy: "#eab308",
  Law: "#f59e0b",
  Metric: "#14b8a6",
  Asset: "#ec4899",
  Instrument: "#d946ef",
  Location: "#84cc16",
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
    PANIC: { bg: 'rgba(255,71,87,0.15)', text: 'var(--red)', border: 'rgba(255,71,87,0.3)' },
    fear: { bg: 'rgba(249,115,22,0.15)', text: '#fb923c', border: 'rgba(249,115,22,0.3)' },
    agitated: { bg: 'rgba(245,166,35,0.15)', text: 'var(--amber)', border: 'rgba(245,166,35,0.3)' },
    calm: { bg: 'rgba(107,114,128,0.15)', text: 'var(--text2)', border: 'rgba(107,114,128,0.3)' },
    optimism: { bg: 'rgba(0,245,196,0.12)', text: 'var(--cyan)', border: 'rgba(0,245,196,0.25)' },
    EUPHORIA: { bg: 'rgba(0,245,196,0.2)', text: 'var(--cyan)', border: 'rgba(0,245,196,0.4)' },
  };
  const colors = stateColors[state] || stateColors.calm;
  return (
    <div data-testid="emotional-temperature" className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold" style={{background:colors.bg,color:colors.text,border:`1px solid ${colors.border}`}}>
      <span className="uppercase tracking-wider">{state}</span>
      <span style={{opacity:0.7}}>V:{mean_valence > 0 ? "+" : ""}{mean_valence?.toFixed(2)} A:{mean_arousal?.toFixed(2)}</span>
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
    <div data-testid="sentiment-chart" className="rounded-xl p-4" style={{background:'var(--panel)',border:'1px solid var(--border)'}}>
      <p className="text-xs uppercase tracking-wider mb-3" style={{color:'var(--text3)'}}>Sentiment Flow by Round</p>
      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,245,196,0.08)" />
          <XAxis dataKey="name" tick={{ fill: "#8892a4", fontSize: 11 }} />
          <YAxis tick={{ fill: "#8892a4", fontSize: 11 }} domain={[0, 100]} />
          <ReTooltip contentStyle={{ background: "#0b0f1a", border: "1px solid rgba(0,245,196,0.12)", borderRadius: 8 }} />
          <Area type="monotone" dataKey="positive" stackId="1" stroke="#00f5c4" fill="#00f5c4" fillOpacity={0.5} />
          <Area type="monotone" dataKey="neutral" stackId="1" stroke="#4a5568" fill="#4a5568" fillOpacity={0.4} />
          <Area type="monotone" dataKey="negative" stackId="1" stroke="#ff4757" fill="#ff4757" fillOpacity={0.5} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

const Header = ({ onNewSimulation, hasSession, grokActive, user, onSignOut, onShowAccuracy }) => (
  <header className="app-header">
    <div className="logo-wrap">
      <div className="logo-icon-box">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00f5c4" strokeWidth="1.5">
          <circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8" opacity="0.3"/>
          <path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>
        </svg>
      </div>
      <div>
        <div className="logo-name">SwarmSim</div>
        <div className="logo-tagline">Swarm Intelligence Engine</div>
      </div>
    </div>
    <div style={{display:'flex',gap:'12px',alignItems:'center'}}>
      {grokActive && (
        <span data-testid="grok-badge" style={{
          display:'inline-flex',alignItems:'center',gap:'6px',
          padding:'5px 12px',
          background:'rgba(167,139,250,0.12)',
          border:'1px solid rgba(167,139,250,0.25)',
          borderRadius:'99px',
          fontFamily:'var(--mono)',fontSize:'11px',color:'var(--violet)'
        }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 4l16 16M20 4L4 20"/>
          </svg>
          Grok Active
        </span>
      )}
      <button
        data-testid="accuracy-dashboard-btn"
        onClick={onShowAccuracy}
        className="btn-ghost"
        style={{padding:'5px 12px',fontSize:'11px',fontFamily:'var(--mono)'}}
      >
        <Target className="w-3.5 h-3.5 inline mr-1" />
        Accuracy
      </button>
      <span className="badge-live" data-testid="system-status">System Online</span>
      {user && (
        <span className="hidden sm:inline-flex text-xs px-2 py-1 rounded-full border border-sw text-sw2">
          {user.name || user.email}
        </span>
      )}
      {hasSession && (
        <button
          data-testid="new-simulation-button"
          onClick={onNewSimulation}
          className="btn-ghost"
        >
          + New Simulation
        </button>
      )}
      {user && (
        <button
          data-testid="signout-button"
          onClick={onSignOut}
          className="btn-ghost"
        >
          Sign Out
        </button>
      )}
    </div>
  </header>
);

// Step Indicator Component
const StepIndicator = ({ currentStep, completedSteps, onStepClick }) => (
  <div className="steps-bar">
    <div className="steps">
      {STEPS.map((step, index) => {
        const isActive = currentStep === step.id;
        const isCompleted = completedSteps.includes(step.id);
        const isClickable = isCompleted || step.id <= Math.max(...completedSteps, 1);
        const stepNum = String(step.id).padStart(2, '0');
        
        return (
          <div
            key={step.id}
            data-testid={`step-${step.id}-indicator`}
            className={`step ${isCompleted && !isActive ? 'done' : ''} ${isActive ? 'active' : ''}`}
            onClick={() => isClickable && onStepClick(step.id)}
            style={{ cursor: isClickable ? 'pointer' : 'default', opacity: isClickable ? 1 : 0.4 }}
          >
            <div className="step-dot">
              {isCompleted && !isActive ? '✓' : stepNum}
            </div>
            <div className="step-name">{step.name}</div>
          </div>
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
            height: Math.min(420, window.innerHeight - 360)
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
      importance: entity.importance,
      color: ENTITY_COLORS[entity.type] || ENTITY_COLORS.default,
      val: entity.importance === 'High' ? 14 : entity.importance === 'Medium' ? 10 : 6
    }));

    const nodeIds = new Set(nodes.map(n => n.id));
    const links = (graph.relationships || [])
      .map(rel => ({
        source: rel.source_id || rel.source,
        target: rel.target_id || rel.target,
        label: rel.type || rel.label,
        weight: rel.weight || (rel.strength === 'Strong' ? 0.9 : rel.strength === 'Medium' ? 0.6 : 0.3)
      }))
      .filter(link => nodeIds.has(link.source) && nodeIds.has(link.target));

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
    <div className="border rounded-xl overflow-hidden h-full flex flex-col" style={{background:'var(--bg2)',borderColor:'var(--border)'}}>
      <div className="px-4 py-3 border-b flex items-center justify-between" style={{borderColor:'var(--border)',background:'var(--bg)'}}>
        <h3 className="text-sm font-semibold" style={{color:'var(--text)'}}>Graph Relationship Visualization</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="p-1.5 rounded transition-colors"
            style={{color:'var(--text2)'}}
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowLabels(!showLabels)}
            className="flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors"
            style={{
              background: showLabels ? 'var(--cyan-dim)' : 'var(--bg3)',
              color: showLabels ? 'var(--cyan)' : 'var(--text2)'
            }}
          >
            {showLabels ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
            <span>Edge Labels</span>
          </button>
        </div>
      </div>
      
      <div ref={containerRef} className="flex-1 relative" style={{background:'var(--bg)'}}>
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="#06080f"
          nodeLabel={node => `${node.name}\n${node.description || ''}`}
          nodeColor={node => node.color}
          nodeRelSize={6}
          linkColor={() => "rgba(0, 245, 196, 0.15)"}
          linkWidth={link => Math.max(1, link.weight * 3)}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={2}
          linkDirectionalParticleColor={() => "rgba(0, 245, 196, 0.4)"}
          linkLabel={showLabels ? link => link.label : undefined}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 10 / globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.beginPath();
            ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI);
            ctx.fillStyle = node.color;
            ctx.fill();
            if (globalScale > 0.5) {
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillStyle = "#e8edf8";
              ctx.fillText(label, node.x, node.y + 12);
            }
          }}
          cooldownTicks={100}
          onEngineStop={() => graphRef.current?.zoomToFit(400, 50)}
        />
      </div>

      {/* Entity Type Legend */}
      <div className="px-4 py-3 border-t" style={{borderColor:'var(--border)',background:'var(--bg)'}}>
        <p className="text-[10px] uppercase tracking-wider mb-2" style={{color:'var(--text3)'}}>Entity Types</p>
        <div className="flex flex-wrap gap-3">
          {entityTypes.map(({ type, color, count }) => (
            <div key={type} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-xs capitalize" style={{color:'var(--text2)'}}>{type}</span>
              <span className="text-[10px]" style={{color:'var(--text3)'}}>({count})</span>
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
    <div className="terminal-box">
      {logs.map((log, i) => (
        <div key={i} style={{display:'flex',gap:'8px'}}>
          <span className="t-dm">{log.time}</span>
          <span className={log.type === "success" ? "t-gn" : log.type === "error" ? "t-rd" : "t-dm"}>
            {log.message}
          </span>
        </div>
      ))}
      <div ref={logsEndRef} />
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
  const [socialSeed, setSocialSeed] = useState(null);
  const [seedLoading, setSeedLoading] = useState(false);
  const [grokStatus, setGrokStatus] = useState(null);
  const [liveProgress, setLiveProgress] = useState(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState(null);
  const [domain, setDomain] = useState(null);

  const addLog = (message, type = "info") => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    setLogs(prev => [...prev.slice(-20), { time, message, type }]);
  };

  // Check Grok availability on mount
  useEffect(() => {
    axios.get(`${API}/health`).then(res => {
      const grokAvail = res.data.grok_available;
      setGrokStatus(grokAvail ? "active" : "offline");
      addLog(
        grokAvail
          ? "GROK X Search active — real Twitter data ready"
          : "GROK offline — Reddit + Nitter fallback active",
        grokAvail ? "success" : "info"
      );
      addLog("NET Reddit JSON connected. Fallbacks warm.", "info");
    }).catch(() => {
      setGrokStatus("offline");
      addLog("GROK status check failed — fallbacks active", "info");
    });
  }, []);

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

  const handleTemplateSelect = (template) => {
    setMode("live");
    setTopic(template.topic);
    setHorizon(template.horizon);
    setQuery(template.query);
    setSelectedTemplateId(template.id);
    addLog(`Scenario template loaded: ${template.title}`, "success");
  };

  const handleUploadSubmit = async () => {
    if (!file || !query.trim()) return;
    setLoading(true);
    setError(null);
    setLiveProgress(null);
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
    setLiveProgress({
      progress: "Starting live intelligence fetch...",
      progress_step: 0,
      progress_total: 5,
      status: "fetching",
    });
    addLog(`Fetching live data for: ${topic}...`);
    addLog(`Prediction horizon: ${horizon}`);

    try {
      // Kick off background fetch (returns 202 immediately)
      await axios.post(`${API}/sessions/${sessionId}/fetch-live`, {
        topic: topic,
        horizon: horizon,
        prediction_query: query || ''
      }, { timeout: 15000 });
      
      // Poll for status with progress updates
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await axios.get(`${API}/sessions/${sessionId}/live-status`, { timeout: 10000 });
          const data = statusRes.data;
          setLiveProgress({
            progress: data.progress || "Fetching live intelligence...",
            progress_step: data.progress_step || 0,
            progress_total: data.progress_total || 5,
            status: data.status,
          });
          
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
            setLiveProgress({
              progress: "Live intelligence complete",
              progress_step: data.progress_total || 5,
              progress_total: data.progress_total || 5,
              status: "completed",
            });
            if (data.domain) setDomain(data.domain);
            setLoading(false);
          } else if (data.status === "failed") {
            clearInterval(pollInterval);
            const errMsg = data.error || "Live fetch failed";
            addLog(`Error: ${errMsg}`, "error");
            setError(errMsg);
            setLiveProgress(prev => ({ ...(prev || {}), status: "failed", progress: errMsg }));
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
          setLiveProgress(prev => ({ ...(prev || {}), status: "failed", progress: "Live intelligence fetch timed out" }));
          setLoading(false);
        }
      }, 180000);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Failed to start live fetch";
      addLog(`Error: ${errorMsg}`, "error");
      setError(errorMsg);
      setLiveProgress(prev => ({ ...(prev || {}), status: "failed", progress: errorMsg }));
      setLoading(false);
    }
  };

  const handleSubmit = mode === "upload" ? handleUploadSubmit : handleLiveSubmit;

  const handleFetchSocialSeed = async () => {
    if (!topic.trim()) return;
    setSeedLoading(true);
    addLog(`Fetching real social comments for: ${topic}...`);
    try {
      const res = await axios.post(`${API}/sessions/${sessionId}/fetch-social-seed`, {
        topic: topic,
        include_reddit: true,
        include_twitter: true,
        max_comments: 30
      }, { timeout: 45000 });
      setSocialSeed(res.data);
      addLog(`${res.data.message}`, "success");
      if (res.data.powered_by) {
        addLog(`Powered by: ${res.data.powered_by}`, "success");
      }
      if (res.data.grok_brief) {
        addLog(`Grok X Intelligence Brief received`, "success");
      }
      if (res.data.real_sentiment) {
        const s = res.data.real_sentiment;
        addLog(`Real sentiment: ${s.positive}% positive, ${s.negative}% negative, ${s.neutral}% neutral`, "success");
      }
    } catch (err) {
      addLog(`Social seed failed: ${err.response?.data?.detail || err.message}`, "error");
    } finally {
      setSeedLoading(false);
    }
  };

  const exampleQuestions = [
    "Will public support increase or decrease in 6 months?",
    "What is the market sentiment outlook?",
    "How will policy changes impact stakeholders?",
  ];

  const exampleTopics = [
    "Bitcoin price movement",
    "IPL 2026 winner prediction",
    "Bengal Election which party wins",
    "OpenAI GPT-5 impact on tech industry",
    "Bollywood Pushpa 3 box office",
    "US China trade war impact",
    "RBI interest rate decision",
    "Champions League 2026 winner",
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
          <div className="glass-card" style={{padding:'20px'}}>
            <div className="flex items-center gap-3 mb-4">
              {mode === "live" ? (
                <Radio className="w-5 h-5 animate-pulse" style={{color:'var(--cyan)'}} />
              ) : (
                <CheckCircle className="w-5 h-5" style={{color:'var(--cyan)'}} />
              )}
              <h3 className="text-lg font-bold" style={{color:'var(--text)'}}>
                {mode === "live" ? "Live Intelligence Brief" : "Knowledge Graph Extracted"}
              </h3>
              {mode === "live" && (
                <span className="badge-live" style={{fontSize:'10px',padding:'3px 8px'}}>LIVE</span>
              )}
              {domain && (
                <span data-testid="domain-badge" style={{
                  fontSize:'10px',padding:'3px 8px',borderRadius:'99px',
                  background:'rgba(0,245,196,0.08)',
                  border:'1px solid rgba(0,245,196,0.2)',
                  color:'var(--cyan)',fontFamily:'var(--mono)',textTransform:'uppercase',letterSpacing:'.05em'
                }}>{domain.replace('_',' ')}</span>
              )}
            </div>
            
            <p className="text-sm mb-4" style={{color:'var(--text2)'}}>{graph.summary}</p>
            
            {/* Intel Brief Details for Live Mode */}
            {mode === "live" && intelBrief && (
              <div className="mb-4 space-y-3">
                {intelBrief.key_developments && (
                  <div>
                    <p className="text-xs uppercase tracking-wider mb-1" style={{color:'var(--text3)'}}>Key Developments</p>
                    <ul className="space-y-1">
                      {intelBrief.key_developments.slice(0, 3).map((dev, i) => (
                        <li key={i} className="text-xs flex items-start gap-2" style={{color:'var(--text2)'}}>
                          <span style={{color:'var(--cyan)'}}>•</span> {dev}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {intelBrief.data_points && intelBrief.data_points.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {intelBrief.data_points.slice(0, 3).map((dp, i) => (
                      <div key={i} className="px-2 py-1 rounded" style={{background:'var(--bg3)',border:'1px solid var(--border)'}}>
                        <span className="text-[10px]" style={{color:'var(--text3)'}}>{dp.metric}:</span>
                        <span className="text-xs ml-1" style={{color:'var(--text)'}}>{dp.value}</span>
                        <span className={`text-[10px] ml-1`} style={{color: dp.trend === 'up' ? 'var(--cyan)' : dp.trend === 'down' ? 'var(--red)' : 'var(--text2)'}}>
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
              <div data-testid="verified-market-data" className="mb-4 rounded-xl p-3" style={{background:'var(--bg3)',border:'1px solid rgba(0,245,196,0.2)'}}>
                <p className="text-xs uppercase tracking-wider mb-2 flex items-center gap-1.5" style={{color:'var(--cyan)'}}>
                  <CheckCircle className="w-3 h-3" /> Verified Real-Time Data
                </p>
                <div className="space-y-2">
                  {intelBrief.verified_market_data.map((md, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span className="text-sm font-medium" style={{color:'var(--text)'}}>{md.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold mono" style={{color:'var(--text)'}}>{md.currency} {md.price?.toLocaleString()}</span>
                        {md.change_pct != null && (
                          <span className="text-xs font-medium px-1.5 py-0.5 rounded" style={{
                            background: md.change_pct >= 0 ? 'rgba(0,245,196,0.15)' : 'rgba(255,71,87,0.15)',
                            color: md.change_pct >= 0 ? 'var(--cyan)' : 'var(--red)'
                          }}>
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
                <span key={i} className="px-2.5 py-1 text-xs rounded-full" style={{background:'var(--cyan-dim)',color:'var(--cyan)',border:'1px solid rgba(0,245,196,0.2)'}}>
                  {theme}
                </span>
              ))}
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg p-3" style={{background:'var(--bg3)',border:'1px solid var(--border)'}}>
                <div className="text-2xl font-bold mono" style={{color:'var(--cyan)'}}>{graph.entity_count || graph.entities?.length || 0}</div>
                <div className="text-xs" style={{color:'var(--text2)'}}>Entities</div>
              </div>
              <div className="rounded-lg p-3" style={{background:'var(--bg3)',border:'1px solid var(--border)'}}>
                <div className="text-2xl font-bold mono" style={{color:'var(--violet)'}}>{graph.relationship_count || graph.relationships?.length || 0}</div>
                <div className="text-xs" style={{color:'var(--text2)'}}>Relationships</div>
              </div>
            </div>

            {/* Entity Type Breakdown */}
            {graph.entities?.length > 0 && (() => {
              const typeCounts = {};
              const sourceCounts = {};
              graph.entities.forEach(e => {
                const t = e.type || 'Unknown';
                typeCounts[t] = (typeCounts[t] || 0) + 1;
                const s = (e.source || 'brief').split('+')[0];
                sourceCounts[s] = (sourceCounts[s] || 0) + 1;
              });
              const sorted = Object.entries(typeCounts).sort((a,b) => b[1] - a[1]).slice(0, 6);
              const sourceColors = {brief:'var(--cyan)',twitter:'#a855f7',reddit:'#f97316',social:'#3b82f6'};
              return (
                <>
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {sorted.map(([type, count]) => (
                    <span key={type} className="px-2 py-0.5 text-[10px] rounded-full flex items-center gap-1" style={{background:'var(--bg3)',border:'1px solid var(--border)',color:'var(--text2)'}}>
                      <span className="w-1.5 h-1.5 rounded-full" style={{backgroundColor: ENTITY_COLORS[type] || ENTITY_COLORS.default}}/>
                      {type}: {count}
                    </span>
                  ))}
                </div>
                {Object.keys(sourceCounts).length > 1 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {Object.entries(sourceCounts).map(([src, count]) => (
                      <span key={src} className="px-2 py-0.5 text-[10px] rounded-full flex items-center gap-1" style={{background:'var(--bg3)',border:'1px solid var(--border)',color:sourceColors[src] || 'var(--text2)'}}>
                        {src}: {count}
                      </span>
                    ))}
                  </div>
                )}
                </>
              );
            })()}
          </div>

          {/* Entity Preview */}
          <div className="glass-card" style={{padding:'16px'}}>
            <h4 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{color:'var(--text2)'}}>Key Entities</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {(graph.entities || [])
                .slice()
                .sort((a, b) => {
                  const imp = {High: 0, Medium: 1, Low: 2};
                  return (imp[a.importance] ?? 2) - (imp[b.importance] ?? 2);
                })
                .slice(0, 8)
                .map((entity, i) => (
                <div key={i} className="flex items-center gap-2 p-2 rounded" style={{background:'var(--bg3)',border:'1px solid var(--border)'}}>
                  <div 
                    className="w-2 h-2 rounded-full flex-shrink-0" 
                    style={{ backgroundColor: ENTITY_COLORS[entity.type] || ENTITY_COLORS.default }}
                  />
                  <span className="text-sm font-medium truncate" style={{color:'var(--text)'}}>{entity.name}</span>
                  {entity.importance === 'High' && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded-full ml-auto flex-shrink-0" style={{background:'rgba(239,68,68,0.15)',color:'#ef4444',border:'1px solid rgba(239,68,68,0.3)'}}>HIGH</span>
                  )}
                  <span className="text-[10px] capitalize ml-auto" style={{color:'var(--text3)'}}>{entity.type}</span>
                </div>
              ))}
            </div>
          </div>

          <SystemDashboard logs={logs} />

          {/* Social Seed Panel — only for live mode */}
          {mode === "live" && (
            <div data-testid="social-seed-panel" className="glass-card" style={{padding:'16px'}}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4" style={{color:'var(--amber)'}} />
                  <h4 className="text-sm font-semibold" style={{color:'var(--text)'}}>Real Social Seed</h4>
                  <span className="text-[10px] px-1.5 py-0.5 rounded" style={{color:'var(--text3)',background:'var(--bg3)'}}>optional</span>
                </div>
                <button
                  data-testid="fetch-social-seed-button"
                  onClick={handleFetchSocialSeed}
                  disabled={seedLoading || !topic.trim()}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
                  style={{background:'rgba(245,166,35,0.15)',border:'1px solid rgba(245,166,35,0.3)',color:'var(--amber)'}}
                >
                  {seedLoading ? 'Fetching...' : socialSeed ? 'Re-fetch' : grokStatus === 'active' ? 'Grok X Search + Reddit' : 'Fetch Reddit + Twitter'}
                </button>
              </div>
              <p className="text-xs mb-3" style={{color:'var(--text3)'}}>
                {grokStatus === 'active'
                  ? 'Powered by Grok X Search — fetches real tweets + Reddit comments for grounded simulations.'
                  : 'Seed the simulation with real Reddit/Twitter comments. Agents will react to actual public opinion.'
                }
              </p>

              {socialSeed && socialSeed.comments_fetched > 0 && (
                <div className="space-y-2">
                  {/* Grok X Intelligence Brief */}
                  {socialSeed.grok_brief && (
                    <div style={{
                      background:'rgba(0,245,196,0.04)',
                      border:'1px solid rgba(0,245,196,0.15)',
                      borderRadius:'8px',
                      padding:'8px 10px',
                      marginBottom:'6px'
                    }}>
                      <div style={{
                        fontFamily:'var(--mono)',fontSize:'9px',
                        color:'var(--cyan)',letterSpacing:'0.06em',
                        textTransform:'uppercase',marginBottom:'4px',
                        display:'flex',alignItems:'center',gap:'4px'
                      }}>
                        <span style={{width:'4px',height:'4px',borderRadius:'50%',background:'var(--cyan)',display:'inline-block',animation:'pulse-dot 1.5s infinite'}}/>
                        Grok X Brief
                      </div>
                      <p style={{fontSize:'11px',color:'var(--text2)',lineHeight:'1.6'}}>{socialSeed.grok_brief}</p>
                    </div>
                  )}
                  <div className="flex items-center gap-3 text-xs">
                    <span className="font-medium" style={{color:'var(--cyan)'}}>{socialSeed.comments_fetched} comments</span>
                    <span style={{color:'var(--text3)'}}>|</span>
                    <span style={{color:'var(--text2)'}}>{socialSeed.sources?.join(', ')}</span>
                  </div>
                  <div className="flex gap-2 text-xs">
                    <span className="px-2 py-0.5 rounded" style={{background:'rgba(16,185,129,0.15)',color:'#34d399'}}>
                      {socialSeed.real_sentiment?.positive || 0}% positive
                    </span>
                    <span className="px-2 py-0.5 rounded" style={{background:'rgba(255,71,87,0.15)',color:'var(--red)'}}>
                      {socialSeed.real_sentiment?.negative || 0}% negative
                    </span>
                    <span className="px-2 py-0.5 rounded" style={{background:'rgba(107,114,128,0.15)',color:'var(--text2)'}}>
                      {socialSeed.real_sentiment?.neutral || 0}% neutral
                    </span>
                  </div>
                  {socialSeed.sample?.slice(0, 3).map((c, i) => (
                    <div key={i} className="rounded-lg p-2 text-xs" style={{background:'var(--bg3)',border:'1px solid var(--border)'}}>
                      <div className="flex items-center gap-1.5 mb-1">
                        <span className="font-medium" style={{color: c.platform === 'Reddit' ? '#fb923c' : '#60a5fa'}}>
                          {c.platform}
                        </span>
                        <span style={{color:'var(--text3)'}}>@{c.author}</span>
                        {c.score > 0 && <span className="ml-auto" style={{color:'var(--text3)'}}>{c.score} pts</span>}
                      </div>
                      <p className="line-clamp-2" style={{color:'var(--text2)'}}>{c.content}</p>
                    </div>
                  ))}
                  {/* Powered by badge */}
                  {socialSeed.powered_by && (
                    <div style={{textAlign:'center',fontFamily:'var(--mono)',fontSize:'10px',color:'var(--text3)',marginTop:'4px'}}>
                      Powered by {socialSeed.powered_by}
                    </div>
                  )}
                </div>
              )}
              {socialSeed && socialSeed.comments_fetched === 0 && (
                <p className="text-xs" style={{color:'var(--amber)'}}>No social data found. Simulation will proceed without seeding.</p>
              )}
            </div>
          )}
          
          <button
            data-testid="continue-to-agents-button"
            className="btn-primary"
            onClick={() => onComplete(graph)}
          >
            Continue — Generate Agents <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4">
      <LandingOnboarding onStart={() => document.querySelector('[data-testid="mode-live"]')?.scrollIntoView({ behavior: "smooth", block: "center" })} />
      <ScenarioTemplates
        selectedId={selectedTemplateId}
        onSelect={handleTemplateSelect}
      />

      {/* Stats Row */}
      <div className="stats-row">
        {[
          {val:'1,247',label:'Simulations Run'},
          {val:'38K',label:'Agents Deployed'},
          {val:'892',label:'Predictions Made'},
          {val:'78%',label:'Accuracy Rate'},
        ].map(s => (
          <div key={s.label} className="stat-cell">
            <span className="stat-val">{s.val}</span>
            <span className="stat-lab">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="content-grid">
        {/* LEFT COLUMN */}
        <div className="animate-fadeUp">
          {/* Hero */}
          <div className="upload-hero">
            <div className="hero-tag">
              <svg width="8" height="8" viewBox="0 0 8 8" fill="#00f5c4"><circle cx="4" cy="4" r="4"/></svg>
              Mission Briefing — Phase 01
            </div>
            <h1>{mode === "live" ? "Live Intelligence Mode" : "Feed the Swarm"}</h1>
            <p>
              {mode === "live"
                ? "Fetch real-time data from the web and simulate market reactions."
                : "Drop any document or pull live intelligence. Our AI agents will debate, polarize, and predict."
              }
            </p>
          </div>

          {/* Mode Tabs */}
          <div className="tab-row" style={{justifyContent:'center',marginBottom:'24px'}}>
            <div
              data-testid="mode-upload"
              className={`tab ${mode==='upload'?'active':''}`}
              onClick={() => setMode("upload")}
            >
              <Upload className="w-4 h-4" /> Document Upload
            </div>
            <div
              data-testid="mode-live"
              className={`tab ${mode==='live'?'active':''}`}
              onClick={() => setMode("live")}
            >
              <Radio className="w-4 h-4" /> Live Intelligence <span className="badge-new" style={{marginLeft:'4px'}}>NEW</span>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg flex items-center gap-3 text-sm" style={{background:'rgba(255,71,87,0.1)',border:'1px solid rgba(255,71,87,0.2)',color:'var(--red)'}}>
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Main Glass Card */}
          <div className="glass-card">
            {mode === "upload" ? (
              <>
                {/* Upload Zone */}
                <div
                  data-testid="upload-dropzone"
                  className={`upload-zone scan-zone ${dragActive ? 'drag-over' : ''}`}
                  onClick={() => fileInputRef.current?.click()}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
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
                      <div className="upload-icon-wrap" style={{borderColor:'var(--cyan)',background:'var(--cyan-dim)'}}>
                        <FileText className="w-6 h-6" style={{color:'var(--cyan)'}} />
                      </div>
                      <div className="upload-title">{file.name}</div>
                      <div className="upload-sub" style={{color:'var(--cyan)'}}>{(file.size / 1024).toFixed(1)} KB — Ready to process</div>
                    </div>
                  ) : (
                    <>
                      <div className="upload-icon-wrap">
                        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#00f5c4" strokeWidth="1.5" strokeLinecap="round">
                          <polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/>
                          <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
                        </svg>
                      </div>
                      <div className="upload-title">Drop your intelligence file</div>
                      <div className="upload-sub">PDF, TXT, DOCX, MD, or Images — max 10MB</div>
                      <div className="file-badges">
                        {['PDF','TXT','DOCX','MD','Images'].map(f => (
                          <span key={f} className="file-badge">{f}</span>
                        ))}
                      </div>
                    </>
                  )}
                </div>

                {/* Prediction Question */}
                <div style={{padding:'0 20px 16px'}}>
                  <div className="field-label">
                    <Target className="w-3.5 h-3.5" /> Prediction Question
                  </div>
                  <textarea
                    data-testid="prediction-query-input"
                    className="field"
                    rows={2}
                    placeholder="What do you want to predict? Be specific..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    style={{resize:'none'}}
                  />
                  <div className="mt-3 flex flex-wrap gap-2">
                    {exampleQuestions.map((q, i) => (
                      <button
                        key={i}
                        onClick={() => setQuery(q)}
                        className="text-xs px-3 py-1.5 rounded-full transition-all"
                        style={{background:'var(--bg3)',color:'var(--text2)',border:'1px solid var(--border)'}}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>

                {/* CTA */}
                <div style={{padding:'0 20px 20px'}}>
                  <button
                    data-testid="extract-graph-button"
                    className="btn-primary"
                    onClick={handleSubmit}
                    disabled={!file || !query.trim() || loading}
                  >
                    {loading ? (
                      <><Loader2 className="w-5 h-5 animate-spin" /> Analyzing Document...</>
                    ) : (
                      <><Zap className="w-5 h-5" /> Extract Knowledge Graph</>
                    )}
                  </button>
                </div>
              </>
            ) : (
              /* Live Intelligence Mode */
              <>
                <div style={{padding:'20px'}}>
                  <div className="space-y-5">
                    {/* Topic Input */}
                    <div>
                      <div className="field-label">
                        <Globe className="w-3.5 h-3.5" /> Topic to Track
                      </div>
                      <input
                        data-testid="topic-input"
                        type="text"
                        className="field"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder="e.g., Bengal Election winner, Bitcoin price, IPL 2026, Tesla earnings..."
                      />
                      <div className="mt-3 flex flex-wrap gap-2">
                        {exampleTopics.map((t, i) => (
                          <button
                            key={i}
                            onClick={() => setTopic(t)}
                            className="text-xs px-3 py-1.5 rounded-full transition-all"
                            style={{background:'var(--bg3)',color:'var(--text2)',border:'1px solid var(--border)'}}
                          >
                            {t}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Prediction Horizon */}
                    <div>
                      <div className="field-label">
                        <Clock className="w-3.5 h-3.5" /> Prediction Horizon
                      </div>
                      <div className="horizon-grid">
                        {PREDICTION_HORIZONS.map((h) => (
                          <div
                            key={h}
                            className={`horizon-pill ${horizon === h ? 'active' : ''}`}
                            onClick={() => setHorizon(h)}
                          >
                            {h}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Custom Question */}
                    <div>
                      <div className="field-label">
                        <Target className="w-3.5 h-3.5" /> Custom Question <span className="opt">optional</span>
                      </div>
                      <input
                        data-testid="live-query-input"
                        type="text"
                        className="field"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Leave blank for auto-generated question..."
                      />
                    </div>
                  </div>
                </div>

                {/* Social Seed Button */}
                <div style={{padding:'0 20px 16px'}}>
                  <div className="section-div" style={{marginBottom:'12px'}}>or seed from live social data</div>
                  <button className="btn-violet" onClick={handleFetchSocialSeed} disabled={seedLoading || !topic.trim()}>
                    {seedLoading ? 'Fetching social data...' : grokStatus === 'active' ? '🔍 Seed with Grok X Search + Reddit' : '🌐 Seed with Real Reddit + Twitter'}
                  </button>
                  {socialSeed && socialSeed.comments_fetched > 0 && (
                    <div className="mt-3 space-y-2 text-xs">
                      {/* Grok X Intelligence Brief */}
                      {socialSeed.grok_brief && (
                        <div data-testid="grok-brief" style={{
                          background:'rgba(0,245,196,0.04)',
                          border:'1px solid rgba(0,245,196,0.15)',
                          borderRadius:'10px',
                          padding:'10px 12px',
                          marginBottom:'8px'
                        }}>
                          <div style={{
                            fontFamily:'var(--mono)',fontSize:'9px',
                            color:'var(--cyan)',letterSpacing:'0.08em',
                            textTransform:'uppercase',marginBottom:'6px',
                            display:'flex',alignItems:'center',gap:'6px'
                          }}>
                            <span style={{width:'5px',height:'5px',borderRadius:'50%',background:'var(--cyan)',display:'inline-block',animation:'pulse-dot 1.5s infinite'}}/>
                            Grok X Intelligence Brief
                          </div>
                          <p style={{fontSize:'11px',color:'var(--text2)',lineHeight:'1.65'}}>{socialSeed.grok_brief}</p>
                        </div>
                      )}
                      <div className="flex items-center gap-3">
                        <span style={{color:'var(--cyan)'}} className="font-medium">{socialSeed.comments_fetched} comments</span>
                        <span style={{color:'var(--text3)'}}>|</span>
                        <span style={{color:'var(--text2)'}}>{socialSeed.sources?.join(', ')}</span>
                      </div>
                      <div className="flex gap-2">
                        <span className="px-2 py-0.5 rounded" style={{background:'rgba(16,185,129,0.15)',color:'#34d399'}}>{socialSeed.real_sentiment?.positive || 0}% positive</span>
                        <span className="px-2 py-0.5 rounded" style={{background:'rgba(255,71,87,0.15)',color:'var(--red)'}}>{socialSeed.real_sentiment?.negative || 0}% negative</span>
                        <span className="px-2 py-0.5 rounded" style={{background:'rgba(107,114,128,0.15)',color:'var(--text2)'}}>{socialSeed.real_sentiment?.neutral || 0}% neutral</span>
                      </div>
                      {/* Powered by badge */}
                      {socialSeed.powered_by && (
                        <div data-testid="powered-by-badge" style={{textAlign:'center',fontFamily:'var(--mono)',fontSize:'10px',color:'var(--text3)',marginTop:'4px'}}>
                          Powered by {socialSeed.powered_by}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Submit */}
                <div style={{padding:'0 20px 20px'}}>
                  <button
                    data-testid="fetch-live-button"
                    className="btn-primary"
                    onClick={handleSubmit}
                    disabled={!topic.trim() || loading}
                  >
                    {loading ? (
                      <><Loader2 className="w-5 h-5 animate-spin" /> Fetching Live Data...</>
                    ) : (
                      <><Radio className="w-5 h-5" /> Fetch & Analyze</>
                    )}
                  </button>
                </div>

                {liveProgress && (
                  <div style={{padding:'0 20px 20px'}}>
                    <ProgressStatusCard
                      title="Live Intelligence Progress"
                      subtitle={liveProgress.progress}
                      detail={error}
                      current={liveProgress.progress_step}
                      total={liveProgress.progress_total}
                      status={liveProgress.status === "completed" ? "done" : liveProgress.status === "failed" ? "error" : "running"}
                    />
                  </div>
                )}
              </>
            )}

            {/* Terminal */}
            <div style={{padding:'0 20px 20px'}}>
              <SystemDashboard logs={logs} />
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN — Info Cards + Cost */}
        <div className="animate-fadeUp-d1">
          <div style={{fontSize:'10px',fontFamily:'var(--mono)',color:'var(--text3)',letterSpacing:'0.08em',textTransform:'uppercase',marginBottom:'12px'}}>
            What happens next
          </div>

          {[
            {icon:'🧠',bg:'rgba(0,245,196,0.08)',title:'AI Knowledge Extraction',desc:'Claude maps entities and relationships into a live knowledge graph.'},
            {icon:'👥',bg:'rgba(167,139,250,0.1)',title:'Agent Swarm Generated',desc:'10-300 AI personas with beliefs, occupations, and emotional states.'},
            {icon:'⚡',bg:'rgba(245,166,35,0.1)',title:'Multi-Round Simulation',desc:'Agents debate, react, shift beliefs. Herd and coalitions emerge.'},
            {icon:'📊',bg:'rgba(59,130,246,0.1)',title:'Prediction Report',desc:'Confidence scores, factions, risks, and alternative scenario branches.'},
          ].map(c => (
            <div key={c.title} className="info-card">
              <div className="info-card-icon" style={{background:c.bg}}>{c.icon}</div>
              <div>
                <h3>{c.title}</h3>
                <p>{c.desc}</p>
              </div>
            </div>
          ))}

          {/* Cost Estimate */}
          <div className="cost-card">
            <div className="field-label" style={{marginBottom:'10px'}}>💰 Estimated Cost</div>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'baseline'}}>
              <span style={{fontSize:'13px',color:'var(--text2)'}}>10 agents · 3 rounds</span>
              <span style={{fontFamily:'var(--mono)',fontSize:'18px',fontWeight:'700',color:'var(--cyan)'}}>~$0.05</span>
            </div>
            <div className="cost-bar"><div className="cost-fill" style={{width:'25%'}}/></div>
            <div style={{fontSize:'11px',color:'var(--text3)'}}>Gemini Flash · Haiku · Sonnet for report only</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Agent Card Component
const AgentCard = ({ agent, showPreview = false }) => (
  <div className="glass-card animate-fade-in" style={{padding:'12px'}}>
    <div className="flex items-start gap-3">
      <span className="text-3xl">{agent.avatar_emoji}</span>
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-bold truncate" style={{color:'var(--text)'}}>{agent.name}</h4>
        <p className="text-[11px] truncate" style={{color:'var(--text2)'}}>{agent.occupation}</p>
        <div className="flex items-center gap-2 mt-1.5">
          <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${PERSONALITY_COLORS[agent.personality_type] || "badge-neutral"}`}>
            {agent.personality_type}
          </span>
          <span className="text-[10px] flex items-center gap-0.5" style={{color:'var(--text3)'}}>
            <Target className="w-2.5 h-2.5" />
            {agent.influence_level}/10
          </span>
        </div>
        {showPreview && agent.initial_stance && (
          <p className="text-[11px] mt-2 line-clamp-2 italic" style={{color:'var(--text2)'}}>
            "{agent.initial_stance}"
          </p>
        )}
      </div>
    </div>
  </div>
);

// Agent Step Component with Preview
const AgentStep = ({ sessionId, graph, onComplete }) => {
  const [numAgents, setNumAgents] = useState(10);
  const [cloneMultiplier, setCloneMultiplier] = useState(10);
  const [silentPop, setSilentPop] = useState(5000);
  const [popConfigured, setPopConfigured] = useState(false);
  const [loading, setLoading] = useState(false);
  const [agents, setAgents] = useState(null);
  const [error, setError] = useState(null);
  const [logs, setLogs] = useState([]);

  const totalPop = numAgents + (numAgents * cloneMultiplier) + silentPop;
  const llmCalls = Math.ceil(numAgents / 10);

  const addLog = (message, type = "info") => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    setLogs(prev => [...prev.slice(-20), { time, message, type }]);
  };

  const configurePopulation = async () => {
    try {
      const res = await axios.post(`${API}/sessions/${sessionId}/configure-population`, {
        tier1_agents: numAgents,
        clone_multiplier: cloneMultiplier,
        silent_population: silentPop,
      });
      addLog(`Population configured: ${res.data.total_simulated.toLocaleString()} total`, "success");
      setPopConfigured(true);
    } catch (err) {
      addLog(`Failed to configure population: ${err.message}`, "error");
    }
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
            // Auto-configure population
            configurePopulation();
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
          <div className="bg-panel border border-sw rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-sw">{agents.length} Agents Generated</h3>
              <span className="text-xs text-sw2">Ready to simulate</span>
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
              <p className="text-center text-xs text-sw3 mt-3">
                +{agents.length - 8} more agents
              </p>
            )}
          </div>

          <SystemDashboard logs={logs} />

          <button
            data-testid="start-simulation-button"
            onClick={() => onComplete(agents)}
            className="btn-primary"
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
        <div className="bg-panel border border-sw rounded-xl p-5">
          <h3 className="text-lg font-bold text-sw mb-4">Generate AI Agents</h3>
          
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
          <div className="bg-sw-bg2 rounded-lg p-3 mb-4 border border-sw">
            <p className="text-xs text-sw3 uppercase tracking-wider mb-1">World Context</p>
            <p className="text-sm text-sw2 line-clamp-4">{graph?.summary}</p>
          </div>

          {/* Agent Count Slider */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-sw">Number of Agents</label>
              <span className="text-xl font-bold text-sw-cyan mono">{numAgents}</span>
            </div>
            <input
              data-testid="agent-count-slider"
              type="range"
              min="10"
              max="300"
              value={numAgents}
              onChange={(e) => setNumAgents(parseInt(e.target.value))}
              className="w-full h-2 bg-sw3 rounded-lg appearance-none cursor-pointer accent-sw-cyan"
            />
            <div className="flex justify-between text-[10px] text-sw3 mt-1">
              <span>10 ($)</span>
              <span>20 ($$)</span>
              <span>50 ($$$)</span>
              <span>300</span>
            </div>
          </div>

          {/* Population Scale */}
          <div data-testid="population-scale" className="bg-panel border border-sw rounded-xl p-4 mb-4">
            <h3 className="text-xs text-sw2 uppercase tracking-wider mb-3">Population Scale</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-sw3 block mb-1">Clone Multiplier ({cloneMultiplier}x)</label>
                <input data-testid="clone-multiplier" type="range" min="1" max="20" value={cloneMultiplier}
                  onChange={(e) => setCloneMultiplier(parseInt(e.target.value))}
                  className="w-full h-1.5 bg-sw3 rounded-lg appearance-none cursor-pointer accent-sw-violet" />
                <div className="flex justify-between text-[10px] text-sw3"><span>1x</span><span>20x</span></div>
              </div>
              <div>
                <label className="text-[10px] text-sw3 block mb-1">Silent Population ({silentPop.toLocaleString()})</label>
                <input data-testid="silent-population" type="range" min="0" max="50000" step="1000" value={silentPop}
                  onChange={(e) => setSilentPop(parseInt(e.target.value))}
                  className="w-full h-1.5 bg-sw3 rounded-lg appearance-none cursor-pointer accent-sw-cyan" />
                <div className="flex justify-between text-[10px] text-sw3"><span>0</span><span>50K</span></div>
              </div>
            </div>
            <div className="mt-3 text-center">
              <span className="text-xs text-sw2">
                <span className="text-sw-cyan font-bold">{numAgents}</span> LLM
                {" x "}<span className="text-purple-400 font-bold">{cloneMultiplier}</span> clones
                {" + "}<span className="text-cyan-400 font-bold">{silentPop.toLocaleString()}</span> silent
                {" = "}<span className="text-sw font-bold text-sm">{totalPop.toLocaleString()}</span> simulated
              </span>
            </div>
          </div>

          {/* Estimate */}
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 mb-4">
            <div className="flex items-center gap-2 text-amber-400 text-xs">
              <Settings className="w-3.5 h-3.5" />
              <span>~{llmCalls} Claude calls/round (same cost as {numAgents} agents)</span>
            </div>
          </div>

          <button
            data-testid="generate-agents-button"
            onClick={handleGenerate}
            disabled={loading}
            className="btn-primary"
            style={{opacity: loading ? 0.6 : 1}}
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
              <p className="text-xs text-sw3 text-center">Creating agent personas...</p>
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
    className={`post-card ${post.is_real ? 'real-post' : ''} ${post.is_hub_post ? 'hub-post' : ''}`}
    style={{marginLeft: isReply ? '16px' : '0', borderLeft: isReply ? '2px solid var(--cyan)' : undefined}}
  >
    <div className="flex items-start gap-2">
      <span className="text-xl">{post.is_real ? (post.platform === 'Reddit' ? '' : '') : post.agent_emoji}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5 flex-wrap">
          <span className="font-semibold text-xs" style={{color:'var(--text)'}}>{post.agent_name}</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded" style={{color:'var(--text3)',background:'var(--bg3)'}}>R{post.round}</span>
          {post.is_real && <span data-testid="real-badge" className="post-badge real">REAL</span>}
          {post.is_hub_post && <span className="post-badge hub">HUB</span>}
          {post.belief_position != null && (
            <span className={`belief-pill ${
              post.belief_position > 0.15 ? 'belief-pos' :
              post.belief_position < -0.15 ? 'belief-neg' :
              'belief-neu'
            }`}>
              {post.belief_position > 0.15 ? '+ support' : post.belief_position < -0.15 ? '- oppose' : '~ undecided'}
            </span>
          )}
          {isReply && (
            <span className="text-[10px]" style={{color:'var(--cyan)'}}>&#8617; {post.reply_to}</span>
          )}
        </div>
        <p className="text-xs" style={{color:'var(--text2)',lineHeight:'1.6'}}>{post.content}</p>
        {post.tier1_reactions && (
          <div className="flex gap-3 mt-1.5 text-[10px]" style={{color:'var(--text3)'}}>
            <span>&#128077; {post.tier1_reactions.likes?.toLocaleString()}</span>
            <span>&#128260; {post.tier1_reactions.shares?.toLocaleString()}</span>
            {post.reach_score != null && (
              <span style={{color: post.viral ? 'var(--amber)' : undefined, fontWeight: post.viral ? '600' : undefined}}>&#9889; {(post.reach_score * 100).toFixed(1)}% reach</span>
            )}
          </div>
        )}
        {post.viral && (
          <span className="inline-flex mt-1 text-[10px] px-1.5 py-0.5 rounded-full" style={{background:'var(--amber-dim)',color:'var(--amber)',border:'1px solid rgba(245,166,35,0.3)'}}>VIRAL</span>
        )}
        {post.agent_tier === "clone" && (
          <span className="inline-flex mt-1 text-[10px] px-1.5 py-0.5 rounded-full" style={{background:'var(--violet-dim)',color:'var(--violet)'}}>ECHO</span>
        )}
      </div>
    </div>
  </div>
);

// Simulation View Component
const SimulationView = ({ sessionId, agents, onComplete, onPostsUpdated }) => {
  const [numRounds, setNumRounds] = useState(3);
  const [simulating, setSimulating] = useState(false);
  const [status, setStatus] = useState(null);
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState(null);
  const [logs, setLogs] = useState([]);
  const [simMeta, setSimMeta] = useState(null);
  const [injectionRefreshKey, setInjectionRefreshKey] = useState(0);
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
            populationSize: statusRes.data.population_size || 0,
            tierBreakdown: statusRes.data.tier_breakdown,
          });
        }
        
        if (postsRes.data.posts.length > posts.length) {
          const newPosts = postsRes.data.posts.slice(posts.length);
          newPosts.forEach(p => {
            addLog(`[${p.platform}] ${p.agent_name}: ${p.content.slice(0, 40)}...`);
          });
        }
        setPosts(postsRes.data.posts);
        onPostsUpdated?.(postsRes.data.posts);

        if (statusRes.data.status === "simulation_done") {
          addLog("Simulation complete!", "success");
          clearInterval(interval);
        } else if (statusRes.data.status === "error") {
          setError("Simulation encountered an error");
          addLog("Simulation error", "error");
          clearInterval(interval);
        }
      } catch {
        // Transient polling failures are expected during long simulations; retry on next tick.
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [simulating, sessionId, posts.length, onPostsUpdated]);

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
          <div className="bg-panel border border-sw rounded-xl p-4">
            <h3 className="text-lg font-bold text-sw mb-4">Participating Agents ({agents?.length || 0})</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 max-h-[450px] overflow-y-auto pr-2">
              {agents?.map((agent) => (
                <div key={agent.id} className="bg-sw3 border border-sw rounded-lg p-2 text-center">
                  <span className="text-2xl">{agent.avatar_emoji}</span>
                  <p className="text-xs text-sw font-medium truncate mt-1">{agent.name}</p>
                  <p className="text-[10px] text-sw3 truncate">{agent.occupation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Simulation Config */}
        <div className="space-y-4">
          <div className="bg-panel border border-sw rounded-xl p-5">
            <h3 className="text-lg font-bold text-sw mb-1">Simulation Settings</h3>
            <p className="text-xs text-sw2 mb-4">Configure rounds and start</p>

            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400 text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-sw">Number of Rounds</label>
                <span className="text-xl font-bold text-sw-cyan mono">{numRounds}</span>
              </div>
              <input
                data-testid="rounds-slider"
                type="range"
                min="3"
                max="10"
                value={numRounds}
                onChange={(e) => setNumRounds(parseInt(e.target.value))}
                className="w-full h-2 bg-sw3 rounded-lg appearance-none cursor-pointer accent-sw-cyan"
              />
              <div className="flex justify-between text-[10px] text-sw3 mt-1">
                <span>3 (fast)</span>
                <span>5 (balanced)</span>
                <span>10 (deep)</span>
              </div>
            </div>

            <div data-testid="cost-estimate" className="bg-sw-bg3/60 rounded-lg p-3 mb-4 flex items-center justify-between">
              <span className="text-xs text-sw2">Estimated cost</span>
              <span className="text-sm font-mono font-bold text-sw-cyan">
                ~${(0.02 + Math.ceil((agents?.length || 10) / 10) * 0.003 + Math.ceil((agents?.length || 10) / 10) * numRounds * 0.004).toFixed(3)}
              </span>
            </div>

            <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 mb-4">
              <p className="text-amber-400 text-xs">
                Estimated time: ~{numRounds * 20} seconds
              </p>
            </div>

            <button
              data-testid="run-simulation-button"
              onClick={startSimulation}
              className="btn-primary"
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
      <ProgressStatusCard
        title={isDone ? "Simulation Complete" : "Simulation Running"}
        subtitle={isDone ? "All rounds completed" : `Round ${status?.current_round || 0} of ${status?.total_rounds || numRounds}`}
        detail={error || (simMeta?.populationSize ? `${simMeta.populationSize.toLocaleString()} population members represented` : "Generating and polling posts in real time")}
        current={status?.current_round || 0}
        total={status?.total_rounds || numRounds}
        countLabel={`${posts.length} posts`}
        status={error ? "error" : isDone ? "done" : "running"}
      />

      {/* AI Enhancement Panels */}
      {simMeta && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {/* Emotional Temperature */}
          <div className="bg-panel rounded-xl p-3 border border-sw">
            <p className="text-xs text-sw2 uppercase tracking-wider mb-2">Crowd Emotion</p>
            <EmotionalTemperatureGauge data={simMeta.emotionalSummary} />
          </div>
          {/* Belief Distribution */}
          {simMeta.beliefSummary && (
            <div className="bg-panel rounded-xl p-3 border border-sw">
              <p className="text-xs text-sw2 uppercase tracking-wider mb-2">Belief Distribution</p>
              <div className="flex gap-2 text-xs">
                <span className="bg-green-500/15 text-sw-cyan px-2 py-1 rounded">{simMeta.beliefSummary.support}% support</span>
                <span className="bg-red-500/15 text-red-400 px-2 py-1 rounded">{simMeta.beliefSummary.opposition}% oppose</span>
                <span className="bg-sw3/15 text-sw2 px-2 py-1 rounded">{simMeta.beliefSummary.undecided}% undecided</span>
              </div>
            </div>
          )}
          {/* Network & Population */}
          {(simMeta.networkStats || simMeta.tierBreakdown) && (
            <div className="bg-panel rounded-xl p-3 border border-sw">
              <p className="text-xs text-sw2 uppercase tracking-wider mb-2">Population</p>
              <div className="flex flex-wrap gap-1.5 text-xs">
                {simMeta.tierBreakdown && (
                  <>
                    <span className="bg-sw-cyan/15 text-sw-cyan px-2 py-1 rounded">{simMeta.tierBreakdown.tier1} LLM</span>
                    <span className="bg-purple-500/15 text-purple-400 px-2 py-1 rounded">{simMeta.tierBreakdown.tier2} echo</span>
                    <span className="bg-cyan-500/15 text-cyan-400 px-2 py-1 rounded">{(simMeta.tierBreakdown.tier3 || 0).toLocaleString()} reacting</span>
                  </>
                )}
                {simMeta.populationSize > 0 && (
                  <span className="bg-white/10 text-sw px-2 py-1 rounded font-semibold">{simMeta.populationSize.toLocaleString()} total</span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sentiment Chart */}
      {posts.length > 5 && <SentimentChart posts={posts} />}

      {/* Dual Feed Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SimulationFeed
          title="Twitter Feed"
          icon={<Twitter className="w-4 h-4 text-sw-cyan" />}
          posts={twitterPosts}
          feedRef={twitterFeedRef}
          isDone={isDone}
          renderPost={(post, i) => <PostCard key={i} post={post} isReply={post.post_type === "reply"} />}
        />
        <SimulationFeed
          title="Reddit Feed"
          icon={<div className="w-4 h-4 rounded-full bg-orange-500 flex items-center justify-center text-sw text-[10px] font-bold">R</div>}
          posts={redditPosts}
          feedRef={redditFeedRef}
          isDone={isDone}
          renderPost={(post, i) => <PostCard key={i} post={post} isReply={post.post_type === "reply"} />}
        />
      </div>

      <SystemDashboard logs={logs} />

      {isDone && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <GodViewInjectionPanel
              apiBase={API}
              sessionId={sessionId}
              onInjected={async () => {
                const [statusRes, postsRes] = await Promise.all([
                  axios.get(`${API}/sessions/${sessionId}/simulation-status`),
                  axios.get(`${API}/sessions/${sessionId}/posts`),
                ]);
                setStatus(statusRes.data);
                setPosts(postsRes.data.posts);
                onPostsUpdated?.(postsRes.data.posts);
                addLog("Injected variable rounds complete", "success");
              }}
            />
            <SimulationReplayTimeline
              posts={posts}
              narratives={simMeta?.roundNarratives || []}
            />
          </div>
          <button
            data-testid="generate-report-button"
            onClick={() => onComplete(posts)}
            className="btn-primary"
          >
            Generate Report
            <BarChart3 className="w-4 h-4" />
          </button>
          <button
            data-testid="extend-simulation-button"
            onClick={async () => {
              try {
                const res = await axios.post(
                  `${API}/sessions/${sessionId}/extend`,
                  { additional_rounds: 3 }
                );
                if (res.data.status === 'extending') {
                  setSimulating(true);
                }
              } catch (e) {
                setError('Failed to extend simulation');
              }
            }}
            className="btn-secondary"
          >
            + Extend 3 more rounds (skip regeneration, ~$0.02)
          </button>
        </div>
      )}
    </div>
  );
};

// Confidence Gauge Component
const ConfidenceGauge = ({ score, confidence }) => {
  const percentage = Math.round(score * 100);
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (score * circumference);
  const color = confidence === "High" ? "#00f5c4" : confidence === "Medium" ? "#f5a623" : "#ff4757";
  
  return (
    <div className="relative w-28 h-28">
      <svg className="w-full h-full -rotate-90">
        <circle cx="56" cy="56" r="40" fill="none" stroke="var(--bg3)" strokeWidth="8" />
        <circle
          cx="56" cy="56" r="40" fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" className="transition-all duration-1000"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold mono" style={{color:'var(--text)'}}>{percentage}%</span>
        <span className="text-[10px]" style={{color:'var(--text2)'}}>{confidence}</span>
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
  const [qualityScore, setQualityScore] = useState(null);

  useEffect(() => {
    axios.get(`${API}/sessions/${sessionId}/simulation-status`)
      .then(res => setSessionMeta(res.data))
      .catch(() => {});
  }, [sessionId]);

  // Poll for background critic quality score
  useEffect(() => {
    if (!report) return;
    const timer = setTimeout(async () => {
      try {
        const res = await axios.get(`${API}/sessions/${sessionId}`);
        if (res.data.quality_score) {
          setQualityScore(res.data.quality_score);
        }
      } catch(e) {}
    }, 35000);
    return () => clearTimeout(timer);
  }, [report, sessionId]);

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
        <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4" style={{background:'var(--cyan-dim)'}}>
          <BarChart3 className="w-10 h-10 text-sw-cyan" />
        </div>
        <h2 className="text-2xl font-bold text-sw mb-2">Generate Prediction Report</h2>
        <p className="text-sw2 text-sm mb-6">
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
          className="py-3 px-6 btn-primary text-sw font-semibold rounded-lg flex items-center justify-center gap-2 mx-auto"
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
            <div className="w-20 h-20 rounded-full animate-spin mx-auto" style={{ animationDuration: '3s', background:'linear-gradient(135deg, var(--cyan), var(--violet))' }}>
              <div className="absolute inset-2 rounded-full" style={{background:'var(--bg)'}} />
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl">🧠</span>
            </div>
          </div>
          <h2 className="text-xl font-bold text-sw mt-6 mb-2">ReportAgent Analyzing...</h2>
          <p className="text-sw2 text-sm">Processing simulation data and generating insights</p>
        </div>

        {/* Skeleton Report Preview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-4">
            <SkeletonCard />
            <SkeletonCard />
          </div>
          <div className="space-y-4">
            <SkeletonCard />
            <div className="bg-panel border border-sw rounded-xl p-6 space-y-3">
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
      {/* Prediction Outcome Badge */}
      <PredictionOutcomeBadge sessionId={sessionId} />

      {/* Header with Confidence */}
      <div className="bg-panel border border-sw rounded-xl p-5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex-1">
            <p className="text-xs text-sw3 uppercase tracking-wider mb-1">Predicted Outcome</p>
            <p className="text-xl font-bold text-sw mb-2">{report.prediction?.outcome}</p>
            <p className="text-sm text-sw2">Timeframe: {report.prediction?.timeframe}</p>
          </div>
          <ConfidenceGauge 
            score={report.prediction?.confidence_score || 0.5}
            confidence={report.prediction?.confidence}
          />
        </div>
        {/* Simulation Quality Badge (from report or background critic) */}
        {(report.quality_score != null || qualityScore) && (
          <div data-testid="quality-score-badge" className={`mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${
            (qualityScore || report.quality_score) >= 8 ? 'bg-emerald-500/15 border-emerald-500/40 text-sw-cyan' :
            (qualityScore || report.quality_score) >= 6 ? 'bg-amber-500/15 border-amber-500/40 text-amber-400' :
            'bg-red-500/15 border-red-500/40 text-red-400'
          }`}>
            <Shield className="w-3.5 h-3.5" />
            Quality: {qualityScore || report.quality_score}/10
            {report.overconfident && <span className="text-yellow-400 ml-1">(overconfident)</span>}
          </div>
        )}
      </div>

      <PredictionQualityPanel quality={report.prediction_quality} />
      <EnsembleForecastPanel ensemble={report.ensemble_forecast} />
      <EvidenceLedgerPanel ledger={report.evidence_ledger} />

      {/* Live Stock Data */}
      {['financial', 'crypto', 'macro', 'real_estate'].includes((report.domain || '').toLowerCase()) && report.stock_data && report.stock_data.length > 0 && (
        <div data-testid="stock-data-section" className="glass-card" style={{padding:'16px'}}>
          <h3 className="text-sm font-bold mb-3" style={{color:'var(--text)',fontFamily:'var(--display)'}}>
            Live Market Data
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {report.stock_data.map((s, i) => {
              const ccy = {INR:'Rs ',USD:'$',GBP:'GBP ',EUR:'EUR '}[s.currency] || (s.currency + ' ');
              const isUp = s.change_pct >= 0;
              return (
                <div key={i} className="rounded-xl p-3" style={{background:'var(--bg3)',border:'1px solid var(--border)'}}>
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <div className="text-xs font-bold" style={{color:'var(--text)'}}>{s.name}</div>
                      <div className="text-[10px] mono" style={{color:'var(--text3)'}}>{s.ticker} · {s.exchange}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold mono" style={{color:'var(--text)'}}>{ccy}{s.last_close?.toLocaleString()}</div>
                      <div className="text-[10px] font-semibold mono" style={{color: isUp ? 'var(--cyan)' : 'var(--red)'}}>
                        {isUp ? '+' : ''}{s.change_pct?.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]" style={{color:'var(--text2)'}}>
                    <div>MA5: <span className="mono" style={{color: s.above_ma5 ? 'var(--cyan)' : 'var(--red)'}}>{ccy}{s.ma5?.toLocaleString()}</span></div>
                    <div>MA20: <span className="mono" style={{color: s.above_ma20 ? 'var(--cyan)' : 'var(--red)'}}>{ccy}{s.ma20?.toLocaleString()}</span></div>
                    <div>Support: <span className="mono">{ccy}{s.support?.toLocaleString()}</span></div>
                    <div>Resist: <span className="mono">{ccy}{s.resistance?.toLocaleString()}</span></div>
                    <div>RSI: <span className="mono" style={{color: s.rsi < 30 ? 'var(--cyan)' : s.rsi > 70 ? 'var(--red)' : 'var(--text2)'}}>{s.rsi}</span></div>
                    <div>Vol: <span className="mono">{s.vol_ratio?.toFixed(1)}x</span></div>
                  </div>
                  <div className="mt-2 text-[10px] font-semibold px-2 py-1 rounded text-center" style={{
                    background: s.trend?.includes('UP') ? 'rgba(0,245,196,0.1)' : s.trend?.includes('DOWN') ? 'rgba(255,71,87,0.1)' : 'rgba(107,114,128,0.1)',
                    color: s.trend?.includes('UP') ? 'var(--cyan)' : s.trend?.includes('DOWN') ? 'var(--red)' : 'var(--text2)'
                  }}>
                    {s.trend}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Simulation Story Arc & AI Insights */}
      {sessionMeta && (sessionMeta.round_narratives?.length > 0 || sessionMeta.emotional_summary) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          {/* Story Arc */}
          {sessionMeta.round_narratives?.length > 0 && (
            <div className="bg-panel border border-sw rounded-xl p-4">
              <h3 data-testid="story-arc" className="text-sm font-bold text-sw mb-2">Simulation Story Arc</h3>
              <div className="space-y-1.5">
                {sessionMeta.round_narratives.map((n, i) => (
                  <p key={i} className="text-xs text-sw2 leading-relaxed">
                    <span className="text-sw-cyan font-medium">{n.startsWith("R") || n.startsWith("BREAKING") ? "" : `Round ${i+1}: `}</span>{n}
                  </p>
                ))}
              </div>
            </div>
          )}
          {/* Emotional Temperature & Belief Summary */}
          <div className="space-y-3">
            {sessionMeta.emotional_summary && (
              <div className="bg-panel border border-sw rounded-xl p-4">
                <h3 className="text-sm font-bold text-sw mb-2">Final Crowd Emotion</h3>
                <EmotionalTemperatureGauge data={sessionMeta.emotional_summary} />
              </div>
            )}
            {sessionMeta.belief_summary && (
              <div className="bg-panel border border-sw rounded-xl p-4">
                <h3 className="text-sm font-bold text-sw mb-2">Final Belief Distribution</h3>
                <div className="flex gap-2 text-xs flex-wrap">
                  <span className="bg-green-500/15 text-sw-cyan px-2 py-1 rounded">{sessionMeta.belief_summary.support}% support</span>
                  <span className="bg-red-500/15 text-red-400 px-2 py-1 rounded">{sessionMeta.belief_summary.opposition}% oppose</span>
                  <span className="bg-sw3/15 text-sw2 px-2 py-1 rounded">{sessionMeta.belief_summary.undecided}% undecided</span>
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
          <div className="bg-panel border border-sw rounded-xl p-4">
            <h3 className="text-sm font-bold text-sw mb-2">Executive Summary</h3>
            <p className="text-sm text-sw2 leading-relaxed">{report.executive_summary}</p>
          </div>

          {/* Opinion Landscape */}
          <div className="bg-panel border border-sw rounded-xl p-4">
            <h3 className="text-sm font-bold text-sw mb-3">Opinion Landscape</h3>
            
            <div className="flex h-3 rounded-full overflow-hidden mb-2">
              <div className="bg-emerald-500" style={{ width: `${report.opinion_landscape?.support_percentage || 0}%` }} />
              <div className="bg-red-500" style={{ width: `${report.opinion_landscape?.opposition_percentage || 0}%` }} />
              <div className="bg-sw3" style={{ width: `${report.opinion_landscape?.undecided_percentage || 0}%` }} />
            </div>
            <div className="flex justify-between text-[10px]">
              <span className="text-sw-cyan">Support: {report.opinion_landscape?.support_percentage}%</span>
              <span className="text-red-400">Oppose: {report.opinion_landscape?.opposition_percentage}%</span>
              <span className="text-sw2">Undecided: {report.opinion_landscape?.undecided_percentage}%</span>
            </div>
          </div>

          {/* Real vs Simulated Comparison */}
          {report.real_vs_simulated && (
            <div data-testid="real-vs-simulated" className="bg-panel border rounded-xl p-4" style={{borderColor:'rgba(245,166,35,0.3)'}}>
              <div className="flex items-center gap-2 mb-3">
                <Globe className="w-4 h-4 text-orange-400" />
                <h3 className="text-sm font-bold text-sw">Real vs Simulated</h3>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                  report.real_vs_simulated.drift_percentage <= 10 ? 'bg-emerald-500/20 text-sw-cyan' :
                  report.real_vs_simulated.drift_percentage <= 25 ? 'bg-amber-500/20 text-amber-400' :
                  'bg-red-500/20 text-red-400'
                }`}>
                  {report.real_vs_simulated.verdict}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <p className="text-[10px] text-sw3 uppercase tracking-wider mb-1">Real ({report.real_vs_simulated.total_real_comments} comments)</p>
                  <div className="flex gap-1">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-green-500/15 text-sw-cyan">{report.real_vs_simulated.real_sentiment?.positive}% pos</span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/15 text-red-400">{report.real_vs_simulated.real_sentiment?.negative}% neg</span>
                  </div>
                </div>
                <div>
                  <p className="text-[10px] text-sw3 uppercase tracking-wider mb-1">Simulated</p>
                  <div className="flex gap-1">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-green-500/15 text-sw-cyan">{report.real_vs_simulated.simulated_sentiment?.positive}% pos</span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/15 text-red-400">{report.real_vs_simulated.simulated_sentiment?.negative}% neg</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex-1 bg-sw-bg3 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      report.real_vs_simulated.drift_percentage <= 10 ? 'bg-emerald-500' :
                      report.real_vs_simulated.drift_percentage <= 25 ? 'bg-amber-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(100, report.real_vs_simulated.drift_percentage * 2)}%` }}
                  />
                </div>
                <span className="text-xs text-sw2 font-mono">{report.real_vs_simulated.drift_percentage}% drift</span>
              </div>
              <p className="text-[10px] text-sw3 mt-2">Sources: {report.real_vs_simulated.sources?.join(', ')}</p>
            </div>
          )}

          {/* Key Factions */}
          <div className="bg-panel border border-sw rounded-xl p-4">
            <h3 className="text-sm font-bold text-sw mb-3">Key Factions</h3>
            <div className="space-y-2">
              {report.opinion_landscape?.key_factions?.map((faction, i) => (
                <div key={i} className="p-2.5 bg-sw3 rounded-lg border border-sw">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sw text-sm">{faction.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      faction.size === "Large" ? "bg-sw-cyan/20 text-sw-cyan" :
                      faction.size === "Medium" ? "bg-amber-500/20 text-amber-400" :
                      "bg-sw3/20 text-sw2"
                    }`}>
                      {faction.size}
                    </span>
                  </div>
                  <p className="text-xs text-sw2">{faction.stance}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-4">
          <EvidenceLedgerPanel ledger={report.evidence_ledger || []} />

          {/* Risk Factors */}
          {report.risk_factors?.length > 0 && (
            <div className="bg-panel border border-sw rounded-xl p-4">
              <h3 className="text-sm font-bold text-sw mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                Risk Factors
              </h3>
              <div className="space-y-2">
                {report.risk_factors.map((risk, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 rounded bg-red-500/5 border border-red-500/10">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 ${
                      risk.likelihood === "High" ? "bg-red-500/20 text-red-400" :
                      risk.likelihood === "Medium" ? "bg-amber-500/20 text-amber-400" :
                      "bg-sw3/20 text-sw2"
                    }`}>
                      {risk.likelihood}
                    </span>
                    <div>
                      <p className="text-sm text-sw font-medium">{risk.factor}</p>
                      <p className="text-xs text-sw2">{risk.impact}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Turning Points */}
          {report.key_turning_points?.length > 0 && (
            <div className="bg-panel border border-sw rounded-xl p-4">
              <h3 className="text-sm font-bold text-sw mb-3">Key Turning Points</h3>
              <div className="space-y-2">
                {report.key_turning_points.map((point, i) => (
                  <div key={i} className="flex gap-2">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-sw-cyan font-bold text-[10px]" style={{background:'var(--cyan-dim)'}}>
                      R{point.round}
                    </div>
                    <div>
                      <p className="text-sm text-sw">{point.description}</p>
                      <p className="text-xs text-sw2">{point.impact}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Agent Highlights */}
          {report.agent_highlights?.length > 0 && (
            <div className="bg-panel border border-sw rounded-xl p-4">
              <h3 className="text-sm font-bold text-sw mb-3">Agent Highlights</h3>
              <div className="space-y-2">
                {report.agent_highlights.slice(0, 3).map((highlight, i) => (
                  <div key={i} className="p-2.5 bg-sw3 rounded-lg border border-sw">
                    <p className="font-medium text-sw text-sm">{highlight.agent_name}</p>
                    <p className="text-xs text-sw2 mb-1">{highlight.role_in_simulation}</p>
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
          className="btn-secondary flex-1"
        >
          <Download className="w-4 h-4" />
          Download PDF
        </button>
        
        <button
          data-testid="interact-with-agents-button"
          onClick={() => onComplete(report)}
          className="btn-primary flex-1"
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
    <div className="flex h-[600px] border border-sw rounded-xl overflow-hidden bg-panel">
      {/* Sidebar */}
      <div className="w-56 border-r border-sw bg-sw-bg2 overflow-y-auto hidden md:block">
        <div className="p-3 border-b border-sw">
          <h3 className="text-xs font-semibold text-sw2 uppercase tracking-wider">Chat Targets</h3>
        </div>
        
        <button
          data-testid="chat-target-report-agent"
          onClick={() => setSelectedTarget({ type: "report", id: "report_agent", name: "ReportAgent" })}
          className={`w-full p-3 flex items-center gap-2 border-b border-sw transition-colors ${
            selectedTarget.id === "report_agent" ? "bg-sw-cyan/10 border-l-2 border-l-sw-cyan" : "hover:bg-sw3"
          }`}
        >
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-lg" style={{background:'var(--cyan-dim)'}}>
            🧠
          </div>
          <div className="text-left">
            <p className="font-semibold text-sw text-xs">ReportAgent</p>
            <p className="text-[10px] text-sw3">Analysis Expert</p>
          </div>
        </button>

        <div className="p-2">
          <p className="text-[10px] text-sw3 px-2 py-1">Agents ({agents?.length || 0})</p>
        </div>
        {agents?.slice(0, 10).map((agent) => (
          <button
            key={agent.id}
            data-testid={`chat-target-${agent.id}`}
            onClick={() => setSelectedTarget({ type: "agent", id: agent.id, name: agent.name, agent })}
            className={`w-full p-2 flex items-center gap-2 border-b border-sw/50 transition-colors ${
              selectedTarget.id === agent.id ? "bg-sw-cyan/10 border-l-2 border-l-sw-cyan" : "hover:bg-sw3"
            }`}
          >
            <span className="text-xl">{agent.avatar_emoji}</span>
            <div className="text-left min-w-0">
              <p className="font-medium text-sw text-xs truncate">{agent.name}</p>
              <p className="text-[10px] text-sw3 truncate">{agent.occupation}</p>
            </div>
          </button>
        ))}
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="px-4 py-3 border-b border-sw bg-sw-bg2 flex items-center gap-2">
          <span className="text-xl">
            {selectedTarget.type === "report" ? "🧠" : selectedTarget.agent?.avatar_emoji}
          </span>
          <div>
            <h3 className="font-semibold text-sw text-sm">{selectedTarget.name}</h3>
            <p className="text-[10px] text-sw3">
              {selectedTarget.type === "report" ? "Analysis Expert" : selectedTarget.agent?.occupation}
            </p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <div className="text-center text-sw3 py-6">
              <p className="text-sm mb-3">Start a conversation</p>
              <div className="flex flex-wrap justify-center gap-2">
                {quickPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(prompt)}
                    className="text-xs px-2.5 py-1 bg-sw-bg3 hover:bg-sw3 text-sw2 rounded-full transition-colors"
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
                    ? "bg-sw-cyan text-sw-bg font-medium rounded-tr-sm"
                    : "bg-sw-bg3 text-sw2 rounded-tl-sm"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-sw-bg3 text-sw2 px-3 py-2 rounded-2xl rounded-tl-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="p-3 border-t border-sw bg-sw-bg2">
          <div className="flex gap-2">
            <input
              data-testid="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder={`Message ${selectedTarget.name}...`}
              className="flex-1 px-3 py-2 bg-sw-bg3 border border-sw rounded-lg text-sw text-sm placeholder:text-sw3 focus:outline-none focus:border-sw-cyan"
            />
            <button
              data-testid="send-message-button"
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className="px-3 py-2 bg-sw-cyan disabled:bg-sw3 disabled:cursor-not-allowed text-sw-bg rounded-lg transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ── ACCURACY DASHBOARD ──────────────────────────────────────────────────────
const AccuracyDashboard = ({ data, onClose }) => {
  if (!data) return null;
  const wr = data.win_rate || 0;
  const getWrColor = (rate) => rate >= 65 ? 'var(--cyan)' : rate >= 50 ? '#eab308' : '#ef4444';
  const wrColor = getWrColor(wr);

  const getTypeLabels = (predType) => {
    const labels = {
      DIRECTIONAL: { UP: '\u2191 UP', DOWN: '\u2193 DOWN', FLAT: '\u2192 FLAT', UNKNOWN: '?' },
      OUTCOME:     { YES: '\u2713 YES', NO: '\u2717 NO', PARTIAL: '~ PARTIAL', UNKNOWN: 'PENDING', PENDING: 'PENDING' },
      SENTIMENT:   { POSITIVE: '\u2191 POSITIVE', NEGATIVE: '\u2193 NEGATIVE', MIXED: '\u2192 MIXED', UNKNOWN: 'PENDING', PENDING: 'PENDING' },
    };
    return labels[(predType || 'OUTCOME').toUpperCase()] || labels.OUTCOME;
  };

  return (
    <div className="animate-fade-in space-y-4" style={{maxWidth:'1100px',margin:'0 auto'}}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 style={{fontFamily:'var(--display)',fontSize:'24px',fontWeight:'800',color:'var(--text)'}}>
            Prediction Accuracy
          </h1>
          <p className="text-xs mt-1" style={{color:'var(--text2)',fontFamily:'var(--mono)'}}>
            {data.total_predictions} tracked · {data.pending} pending
          </p>
        </div>
        <button data-testid="accuracy-back-btn" className="btn-ghost" onClick={onClose} style={{fontSize:'13px'}}>
          Back to Simulation
        </button>
      </div>

      {/* Global stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { val: `${wr}%`, lab: 'Win Rate', color: wrColor },
          { val: data.total_predictions, lab: 'Total Predictions', color: 'var(--text)' },
          { val: data.total_correct, lab: 'Correct Calls', color: 'var(--cyan)' },
          { val: data.pending, lab: 'Awaiting Outcome', color: '#eab308' },
        ].map((s) => (
          <div key={s.lab} data-testid={`accuracy-stat-${s.lab.toLowerCase().replace(/\s+/g, '-')}`} className="bg-panel border border-sw rounded-xl p-4 text-center">
            <div style={{fontFamily:'var(--mono)',fontSize:'26px',fontWeight:'700',color:s.color}}>{s.val}</div>
            <div className="text-[10px] mt-1 uppercase tracking-wider" style={{color:'var(--text3)'}}>{s.lab}</div>
          </div>
        ))}
      </div>

      {/* Prediction Type breakdown */}
      {data.type_breakdown && Object.keys(data.type_breakdown).length > 0 && (
        <div className="flex gap-3 flex-wrap" data-testid="type-breakdown">
          {Object.entries(data.type_breakdown).map(([type, stats]) => (
            <div key={type} className="bg-panel border border-sw rounded-xl p-3 flex-1 min-w-[120px]">
              <div style={{fontFamily:'var(--mono)',fontSize:'10px',color:'var(--text3)',marginBottom:'4px',textTransform:'uppercase',letterSpacing:'.04em'}}>
                {type.toLowerCase()}
              </div>
              <div style={{fontFamily:'var(--mono)',fontSize:'22px',fontWeight:'700',color:getWrColor(stats.win_rate)}}>
                {stats.win_rate}%
              </div>
              <div className="text-[11px]" style={{color:'var(--text3)'}}>
                {stats.correct}/{stats.total}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Domain breakdown */}
      {Object.keys(data.domain_breakdown).length > 0 && (
        <div className="bg-panel border border-sw rounded-xl overflow-hidden">
          <div className="px-4 py-2.5 border-b border-sw" style={{background:'var(--bg3)',fontFamily:'var(--mono)',fontSize:'10px',color:'var(--text3)',textTransform:'uppercase',letterSpacing:'.06em'}}>
            Accuracy by Domain
          </div>
          {Object.entries(data.domain_breakdown).map(([domain, stats]) => (
            <div key={domain} className="flex items-center gap-3 px-4 py-3 border-b border-sw last:border-b-0">
              <div className="w-28 text-xs capitalize" style={{color:'var(--text2)'}}>{domain.replace('_', ' ')}</div>
              <div className="flex-1 h-2 rounded-full overflow-hidden" style={{background:'var(--bg3)'}}>
                <div style={{width:`${stats.win_rate}%`,height:'100%',background:getWrColor(stats.win_rate),borderRadius:'4px',transition:'width .6s ease'}} />
              </div>
              <div style={{fontFamily:'var(--mono)',fontSize:'12px',fontWeight:'700',width:'48px',textAlign:'right',color:getWrColor(stats.win_rate)}}>{stats.win_rate}%</div>
              <div className="text-[10px] w-14 text-right" style={{color:'var(--text3)'}}>{stats.correct}/{stats.total}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Calibration chart */}
        {data.calibration?.length > 0 && (
          <div className="bg-panel border border-sw rounded-xl p-4">
            <div style={{fontFamily:'var(--mono)',fontSize:'10px',color:'var(--text3)',textTransform:'uppercase',letterSpacing:'.06em',marginBottom:'10px'}}>
              Calibration — Predicted vs Actual (%)
            </div>
            <div className="text-[10px] italic mb-2" style={{color:'var(--text3)'}}>Perfect = diagonal. Above = overconfident.</div>
            {data.calibration.map((row) => (
              <div key={row.bucket} className="flex items-center gap-2 mb-1.5">
                <div style={{width:'50px',fontSize:'10px',color:'var(--text3)',fontFamily:'var(--mono)'}}>{row.bucket}</div>
                <div className="flex-1 relative h-4 rounded" style={{background:'rgba(255,255,255,0.03)'}}>
                  <div className="absolute inset-0 rounded" style={{width:`${row.predicted_pct}%`,background:'rgba(255,255,255,0.06)'}} />
                  <div className="absolute top-0.5 bottom-0.5 left-0 rounded" style={{width:`${row.actual_pct}%`,background:getWrColor(row.actual_pct),transition:'width .6s ease'}} />
                </div>
                <div style={{fontFamily:'var(--mono)',fontSize:'11px',width:'36px',textAlign:'right',color:getWrColor(row.actual_pct)}}>{row.actual_pct}%</div>
              </div>
            ))}
          </div>
        )}

        {/* Top agents */}
        {data.top_agents?.length > 0 && (
          <div className="bg-panel border border-sw rounded-xl p-4">
            <div style={{fontFamily:'var(--mono)',fontSize:'10px',color:'var(--text3)',textTransform:'uppercase',letterSpacing:'.06em',marginBottom:'10px'}}>
              Top Predicting Agents
            </div>
            {data.top_agents.slice(0, 5).map((agent, i) => (
              <div key={`${agent.agent_id || agent.agent_name}-${agent.personality_type || i}`} className="flex items-center gap-2 mb-2">
                <div style={{fontFamily:'var(--mono)',fontSize:'10px',color:'var(--text3)',width:'16px'}}>{i + 1}</div>
                <div className="flex-1">
                  <div className="text-xs font-semibold" style={{color:'var(--text)'}}>{agent.agent_name}</div>
                  <div className="text-[10px]" style={{color:'var(--text3)'}}>{agent.personality_type}</div>
                </div>
                <div style={{fontFamily:'var(--mono)',fontSize:'12px',fontWeight:'700',color:getWrColor(agent.win_rate)}}>{agent.win_rate}%</div>
                <div className="text-[10px]" style={{color:'var(--text3)'}}>({agent.correct_predictions}/{agent.total_predictions})</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent predictions */}
      {data.recent?.length > 0 && (
        <div className="bg-panel border border-sw rounded-xl overflow-hidden">
          <div className="px-4 py-2.5 border-b border-sw" style={{background:'var(--bg3)',fontFamily:'var(--mono)',fontSize:'10px',color:'var(--text3)',textTransform:'uppercase',letterSpacing:'.06em'}}>
            Recent Predictions
          </div>
          {data.recent.map((rec, i) => {
            const typeLabels = getTypeLabels(rec.prediction_type);
            const predLabel = typeLabels[rec.predicted_direction] || rec.predicted_direction;
            const actLabel = typeLabels[rec.actual_direction] || (rec.actual_direction || 'pending');
            const statusColor = rec.direction_correct ? 'var(--cyan)' : rec.status === 'pending' ? '#eab308' : '#ef4444';
            return (
              <div key={rec.id || `${rec.topic || rec.domain}-${rec.created_at || i}`} className="flex items-center gap-3 px-4 py-2.5 border-b border-sw last:border-b-0">
                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{background: statusColor}} />
                <div className="flex-1 text-xs truncate" style={{color:'var(--text)'}}>{rec.topic || rec.domain?.replace('_',' ')}</div>
                <div className="text-[10px] flex-shrink-0" style={{
                  color:'var(--text3)',padding:'2px 6px',background:'rgba(255,255,255,0.05)',
                  borderRadius:'4px',fontFamily:'var(--mono)'
                }}>
                  {(rec.prediction_type || 'outcome').toLowerCase()}
                </div>
                <div className="flex-shrink-0" style={{fontFamily:'var(--mono)',fontSize:'11px',color: rec.direction_correct ? 'var(--cyan)' : 'var(--text3)'}}>
                  {predLabel} → {actLabel}
                </div>
                <div style={{fontFamily:'var(--mono)',fontSize:'11px',color:'var(--text3)',flexShrink:0}}>
                  {rec.composite_score != null
                    ? `${Math.round(rec.composite_score * 100)}pts`
                    : rec.status === 'pending' ? 'awaiting' : '\u2014'}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty state */}
      {data.total_predictions === 0 && (
        <div className="bg-panel border border-sw rounded-xl p-8 text-center">
          <Target className="w-10 h-10 mx-auto mb-3" style={{color:'var(--text3)'}} />
          <p className="text-sm" style={{color:'var(--text2)'}}>No predictions tracked yet.</p>
          <p className="text-xs mt-1" style={{color:'var(--text3)'}}>Complete a simulation to start tracking accuracy.</p>
        </div>
      )}
    </div>
  );
};


// ── PREDICTION OUTCOME BADGE ────────────────────────────────────────────────
const PredictionOutcomeBadge = ({ sessionId }) => {
  const [outcome, setOutcome] = useState(null);

  useEffect(() => {
    if (!sessionId) return;
    const fetchOutcome = async () => {
      try {
        const res = await axios.get(`${API}/sessions/${sessionId}/prediction-outcome`);
        if (res.data.status !== 'not_tracked') setOutcome(res.data);
      } catch (e) { /* ignore */ }
    };
    fetchOutcome();
    const interval = setInterval(fetchOutcome, 60000);
    return () => clearInterval(interval);
  }, [sessionId]);

  if (!outcome) return null;

  if (outcome.status === 'scored') {
    const isCorrect = outcome.direction_correct;
    const score = outcome.composite_score || 0;
    return (
      <div data-testid="prediction-outcome-badge" className="rounded-xl p-4 mb-4 flex items-center gap-3 flex-wrap" style={{
        border: `1px solid ${isCorrect ? 'rgba(0,245,196,0.3)' : 'rgba(239,68,68,0.3)'}`,
        background: isCorrect ? 'rgba(0,245,196,0.05)' : 'rgba(239,68,68,0.05)',
      }}>
        <span className="text-lg" style={{color: isCorrect ? 'var(--cyan)' : '#ef4444'}}>
          {isCorrect ? '✓' : '✗'}
        </span>
        <div className="flex-1">
          <div className="text-sm font-semibold" style={{color: isCorrect ? 'var(--cyan)' : '#ef4444'}}>
            Prediction was {isCorrect ? 'CORRECT' : 'INCORRECT'}
          </div>
          <div className="text-xs mt-0.5" style={{color:'var(--text2)'}}>
            Predicted {outcome.predicted_direction} → Actual {outcome.actual_direction || '?'}
            {outcome.actual_price != null && ` · Price: ${outcome.actual_price.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`}
          </div>
        </div>
        <div className="text-right">
          <div style={{fontFamily:'var(--mono)',fontSize:'20px',fontWeight:'700',
            color: score >= 70 ? 'var(--cyan)' : score >= 40 ? '#eab308' : '#ef4444'
          }}>{Math.round(score)}</div>
          <div className="text-[9px]" style={{color:'var(--text3)',fontFamily:'var(--mono)'}}>SCORE / 100</div>
        </div>
      </div>
    );
  }

  if (outcome.status === 'pending') {
    return (
      <div data-testid="prediction-pending-badge" className="rounded-xl p-3 mb-4 flex items-center gap-2" style={{
        border: '1px solid var(--border)', background: 'var(--bg3)'
      }}>
        <div className="w-2 h-2 rounded-full animate-pulse" style={{background:'#eab308'}} />
        <span className="text-xs" style={{color:'var(--text2)'}}>
          Prediction tracking active — outcome scored automatically at {outcome.score_at ? new Date(outcome.score_at).toLocaleString() : 'scheduled time'}
        </span>
      </div>
    );
  }

  return null;
};


// Main App Component
function App() {
  const [user, setUser] = useState(() => {
    try {
      const stored = window.localStorage.getItem("swarmsim_user");
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      return null;
    }
  });
  const [sessionId, setSessionId] = useState(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [graph, setGraph] = useState(null);
  const [agents, setAgents] = useState(null);
  const [posts, setPosts] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [grokActive, setGrokActive] = useState(false);
  const [showAccuracy, setShowAccuracy] = useState(false);
  const [accuracyData, setAccuracyData] = useState(null);

  const loadAccuracyDashboard = async () => {
    try {
      const res = await axios.get(`${API}/predictions/accuracy`);
      setAccuracyData(res.data);
      setShowAccuracy(true);
    } catch {
      setAccuracyData(null);
      setShowAccuracy(false);
    }
  };

  useEffect(() => {
    setAuthToken(user?.accessToken || null);
  }, [user]);

  const clearAuthenticatedSession = useCallback(() => {
    window.localStorage.removeItem("swarmsim_user");
    setAuthToken(null);
    setUser(null);
    setSessionId(null);
    setCurrentStep(1);
    setCompletedSteps([]);
    setGraph(null);
    setAgents(null);
    setPosts(null);
    setReport(null);
    setError(null);
  }, []);

  const createNewSession = useCallback(async () => {
    if (!user?.accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      // Check Grok availability
      try {
        const health = await axios.get(`${API}/health`);
        setGrokActive(!!health.data.grok_available);
      } catch (e) { /* ignore health check failure */ }

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
      if (err.response?.status === 401) {
        clearAuthenticatedSession();
        return;
      }
      setError("Failed to create session. Please refresh the page.");
    } finally {
      setLoading(false);
    }
  }, [clearAuthenticatedSession, user?.accessToken]);

  useEffect(() => {
    if (user) {
      createNewSession();
    } else {
      setLoading(false);
    }
  }, [createNewSession, user]);

  const handleSignIn = async ({ mode, name, email, password }) => {
    const endpoint = mode === "signup" ? "/auth/signup" : "/auth/signin";
    const response = await axios.post(`${API}${endpoint}`, { name, email, password });
    const profile = response.data.user;
    const accessToken = response.data.access_token;
    const sessionUser = { ...profile, accessToken };
    window.localStorage.setItem("swarmsim_user", JSON.stringify(sessionUser));
    setUser(sessionUser);
  };

  const handleSignOut = clearAuthenticatedSession;

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

  const handlePostsUpdated = useCallback((updatedPosts) => {
    setPosts(updatedPosts);
  }, []);

  useEffect(() => {
    if (!user?.accessToken) return;
    axios.get(`${API}/auth/me`).catch(() => {
      handleSignOut();
    });
  }, [user?.accessToken, handleSignOut]);

  if (!user) {
    return <AuthLandingGate onSignIn={handleSignIn} />;
  }

  if (loading) {
    return (
      <div style={{minHeight:'100vh',background:'var(--bg)',position:'relative',overflow:'hidden'}}>
        <canvas id="bg-canvas" />
        <div className="grid-overlay" />
        <ParticleBackground />
        <div className="relative z-10 flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="relative">
              <div className="w-20 h-20 rounded-full animate-spin mx-auto mb-6" style={{background:'linear-gradient(135deg, var(--cyan), var(--violet))',animationDuration:'2s'}}>
                <div className="absolute inset-2 rounded-full" style={{background:'var(--bg)'}} />
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#00f5c4" strokeWidth="1.5">
                  <circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8" opacity="0.3"/>
                  <path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>
                </svg>
              </div>
            </div>
            <h2 className="text-xl font-bold mb-2" style={{color:'var(--text)',fontFamily:'var(--display)'}}>Initializing SwarmSim</h2>
            <p className="text-sm" style={{color:'var(--text2)'}}>Preparing your prediction engine...</p>
            <div className="mt-6 flex justify-center gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-2 h-2 rounded-full animate-bounce"
                  style={{ background:'var(--cyan)', animationDelay: `${i * 0.15}s` }}
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
      <div style={{minHeight:'100vh',background:'var(--bg)',position:'relative',overflow:'hidden'}}>
        <canvas id="bg-canvas" />
        <div className="grid-overlay" />
        <ParticleBackground />
        <div className="relative z-10 flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4" style={{background:'rgba(255,71,87,0.15)'}}>
              <AlertCircle className="w-10 h-10" style={{color:'var(--red)'}} />
            </div>
            <h2 className="text-xl font-bold mb-2" style={{color:'var(--text)',fontFamily:'var(--display)'}}>Connection Error</h2>
            <p className="mb-4" style={{color:'var(--text2)'}}>{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="btn-primary" style={{width:'auto',padding:'10px 24px'}}
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <canvas id="bg-canvas" />
      <div className="grid-overlay" />
      <ParticleBackground />
      <div className="app-shell">
        <Header
          onNewSimulation={handleNewSimulation}
          hasSession={!!sessionId}
          grokActive={grokActive}
          user={user}
          onSignOut={handleSignOut}
          onShowAccuracy={loadAccuracyDashboard}
        />
        
        {showAccuracy ? (
          <main style={{flex:1,padding:'24px 16px',maxWidth:'1400px',margin:'0 auto',width:'100%'}}>
            <AccuracyDashboard data={accuracyData} onClose={() => setShowAccuracy(false)} />
          </main>
        ) : (
        <>
        <StepIndicator
          currentStep={currentStep}
          completedSteps={completedSteps}
          onStepClick={handleStepClick}
        />

        <main style={{flex:1,padding:'24px 16px',maxWidth:'1400px',margin:'0 auto',width:'100%'}}>
          <div>
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
                onPostsUpdated={setPosts}
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
        </>
        )}

        {/* Ticker Bar */}
        <div className="ticker-bar">
          <div className="ticker-item"><span className="ticker-lbl">NIFTY</span><span className="ticker-up">↑ 22,847</span></div>
          <div className="ticker-item"><span className="ticker-lbl">BTC</span><span className="ticker-up">↑ $84,230</span></div>
          <div className="ticker-item"><span className="ticker-lbl">SENSEX</span><span className="ticker-dn">↓ 75,142</span></div>
          <div className="ticker-item"><span className="ticker-lbl">Sessions today</span><span style={{color:'var(--text2)'}}>—</span></div>
          <div className="ticker-item"><span className="ticker-lbl">Engine</span><span style={{color:'var(--cyan)'}}>Online</span></div>
        </div>
      </div>
    </>
  );
}

export default App;
