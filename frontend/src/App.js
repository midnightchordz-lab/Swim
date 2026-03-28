import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import axios from "axios";
import ForceGraph2D from "react-force-graph-2d";
import {
  Upload, FileText, Users, Play, BarChart3, MessageSquare,
  CheckCircle, Loader2, ArrowRight, Send, AlertCircle,
  Twitter, ChevronRight, Zap, Target, TrendingUp, AlertTriangle,
  Download, RefreshCw, Eye, EyeOff, Settings, Terminal
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
const Header = () => (
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
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [graph, setGraph] = useState(null);
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

  const handleSubmit = async () => {
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

  const exampleQuestions = [
    "Will public support increase or decrease in 6 months?",
    "What is the market sentiment outlook?",
    "How will policy changes impact stakeholders?",
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
              <CheckCircle className="w-5 h-5 text-emerald-400" />
              <h3 className="text-lg font-bold text-white">Knowledge Graph Extracted</h3>
            </div>
            
            <p className="text-gray-300 text-sm mb-4">{graph.summary}</p>
            
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
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Upload Your Seed Document</h2>
        <p className="text-gray-400 text-sm">Upload a document and pose your prediction question</p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div
        data-testid="upload-dropzone"
        onClick={() => fileInputRef.current?.click()}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
          dragActive
            ? "border-blue-500 bg-blue-500/10"
            : file
            ? "border-emerald-500 bg-emerald-500/10"
            : "border-gray-700 hover:border-blue-500 bg-gray-900/50"
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
          <div className="flex flex-col items-center gap-2">
            <FileText className="w-10 h-10 text-emerald-400" />
            <p className="text-white font-medium">{file.name}</p>
            <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <Upload className="w-10 h-10 text-gray-500" />
            <p className="text-white font-medium">Drop your file here or click to browse</p>
            <p className="text-xs text-gray-500">Supports PDF, TXT, DOCX, MD, PNG, JPG, JPEG, WEBP (max 10MB)</p>
          </div>
        )}
      </div>

      <div className="mt-5">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Prediction Question
        </label>
        <textarea
          data-testid="prediction-query-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., Will public support for this policy increase or decrease in the next 6 months?"
          className="w-full h-20 px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
        />
        
        <div className="mt-2 flex flex-wrap gap-2">
          {exampleQuestions.map((q, i) => (
            <button
              key={i}
              onClick={() => setQuery(q)}
              className="text-[11px] px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white rounded-full transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      <button
        data-testid="extract-graph-button"
        onClick={handleSubmit}
        disabled={!file || !query.trim() || loading}
        className="w-full mt-5 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Extracting Knowledge Graph...
          </>
        ) : (
          <>
            <Zap className="w-4 h-4" />
            Extract Knowledge Graph
          </>
        )}
      </button>

      <SystemDashboard logs={logs} />
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
      const response = await axios.post(`${API}/sessions/${sessionId}/generate-agents`, {
        num_agents: numAgents,
      }, { timeout: 120000 });
      addLog(`Successfully created ${response.data.agents.length} agents`, "success");
      setAgents(response.data.agents);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || "Failed to generate agents";
      if (errorMsg.includes("502") || errorMsg.includes("timeout") || errorMsg.includes("Gateway")) {
        setError("Server temporarily busy. Please try again with fewer agents or wait a moment.");
      } else {
        setError(errorMsg);
      }
      addLog(`Error: ${errorMsg}`, "error");
    } finally {
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
              max="50"
              value={numAgents}
              onChange={(e) => setNumAgents(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
            <div className="flex justify-between text-[10px] text-gray-500 mt-1">
              <span>10</span>
              <span>30</span>
              <span>50</span>
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
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
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
        <div className="flex items-center gap-2 mb-0.5">
          <span className="font-semibold text-white text-xs">{post.agent_name}</span>
          <span className="text-[10px] text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">R{post.round}</span>
          {isReply && (
            <span className="text-[10px] text-blue-400">↩ {post.reply_to}</span>
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
      <div className="max-w-md mx-auto text-center py-12">
        <div className="animate-pulse-glow inline-block p-6 rounded-full bg-blue-500/10 mb-4">
          <Loader2 className="w-10 h-10 text-blue-400 animate-spin" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">ReportAgent Analyzing...</h2>
        <p className="text-gray-400 text-sm">Processing simulation data</p>
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
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left Column */}
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

  useEffect(() => {
    const createSession = async () => {
      try {
        const response = await axios.post(`${API}/sessions`);
        setSessionId(response.data.session_id);
      } catch (err) {
        setError("Failed to create session. Please refresh the page.");
      } finally {
        setLoading(false);
      }
    };
    createSession();
  }, []);

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
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-sm">Initializing SwarmSim...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center text-red-400">
          <AlertCircle className="w-10 h-10 mx-auto mb-4" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />
      
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
  );
}

export default App;
