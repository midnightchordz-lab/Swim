import React, { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import {
  Upload, FileText, Users, Play, BarChart3, MessageSquare,
  CheckCircle, Loader2, ArrowRight, Send, AlertCircle,
  Twitter, ChevronRight, Zap, Target, TrendingUp, AlertTriangle
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between h-16">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🐟</span>
          <div>
            <h1 className="text-xl font-black tracking-tighter text-white">SwarmSim</h1>
            <p className="text-xs text-gray-500 tracking-wide">Swarm Intelligence Prediction Engine</p>
          </div>
        </div>
      </div>
    </div>
  </header>
);

// Step Indicator Component
const StepIndicator = ({ currentStep, completedSteps, onStepClick }) => (
  <div className="w-full max-w-4xl mx-auto mb-8 px-4">
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
              className={`flex flex-col items-center gap-2 transition-all duration-200 ${
                isClickable ? "cursor-pointer" : "cursor-not-allowed opacity-50"
              }`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${
                  isActive
                    ? "border-blue-500 bg-blue-500/20 text-blue-400"
                    : isCompleted
                    ? "border-emerald-500 bg-emerald-500/20 text-emerald-400"
                    : "border-gray-700 bg-gray-900 text-gray-500"
                }`}
              >
                {isCompleted && !isActive ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <span className="text-lg">{step.emoji}</span>
                )}
              </div>
              <span
                className={`text-xs font-medium hidden sm:block ${
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

// Upload Step Component
const UploadStep = ({ sessionId, onComplete }) => {
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [graph, setGraph] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

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
    }
  }, []);

  const handleSubmit = async () => {
    if (!file || !query.trim()) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("prediction_query", query);

    try {
      const response = await axios.post(`${API}/sessions/${sessionId}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setGraph(response.data.graph);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to process document");
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
      <div className="max-w-4xl mx-auto animate-fade-in">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <CheckCircle className="w-6 h-6 text-emerald-400" />
            <h3 className="text-xl font-bold text-white">Knowledge Graph Extracted</h3>
          </div>
          
          <p className="text-gray-300 mb-4">{graph.summary}</p>
          
          <div className="flex flex-wrap gap-2 mb-6">
            {graph.themes?.map((theme, i) => (
              <span key={i} className="px-3 py-1 bg-blue-500/10 text-blue-400 text-sm rounded-full border border-blue-500/20">
                {theme}
              </span>
            ))}
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-950 rounded-lg p-4 border border-gray-800">
              <div className="text-3xl font-bold text-blue-400 mono">{graph.entities?.length || 0}</div>
              <div className="text-sm text-gray-400">Entities Extracted</div>
            </div>
            <div className="bg-gray-950 rounded-lg p-4 border border-gray-800">
              <div className="text-3xl font-bold text-emerald-400 mono">{graph.relationships?.length || 0}</div>
              <div className="text-sm text-gray-400">Relationships</div>
            </div>
          </div>
          
          <div className="max-h-48 overflow-y-auto">
            <h4 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wider">Key Entities</h4>
            <div className="space-y-2">
              {graph.entities?.slice(0, 8).map((entity, i) => (
                <div key={i} className="flex items-center gap-3 p-2 bg-gray-950 rounded border border-gray-800">
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    entity.stance === "positive" ? "bg-emerald-500/20 text-emerald-400" :
                    entity.stance === "negative" ? "bg-red-500/20 text-red-400" :
                    "bg-gray-500/20 text-gray-400"
                  }`}>
                    {entity.type}
                  </span>
                  <span className="text-white font-medium">{entity.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <button
          data-testid="continue-to-agents-button"
          onClick={() => onComplete(graph)}
          className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
        >
          Continue → Generate Agents
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Upload Your Seed Document</h2>
        <p className="text-gray-400">Upload a document and pose your prediction question</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-400">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
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
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
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
          onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])}
          className="hidden"
        />
        {file ? (
          <div className="flex flex-col items-center gap-3">
            <FileText className="w-12 h-12 text-emerald-400" />
            <p className="text-white font-medium">{file.name}</p>
            <p className="text-sm text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="w-12 h-12 text-gray-500" />
            <p className="text-white font-medium">Drop your file here or click to browse</p>
            <p className="text-sm text-gray-500">Supports PDF, TXT, DOCX, MD, PNG, JPG, JPEG, WEBP (max 10MB)</p>
          </div>
        )}
      </div>

      <div className="mt-6">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Prediction Question
        </label>
        <textarea
          data-testid="prediction-query-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., Will public support for this policy increase or decrease in the next 6 months?"
          className="w-full h-24 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
        />
        
        <div className="mt-3 flex flex-wrap gap-2">
          {exampleQuestions.map((q, i) => (
            <button
              key={i}
              onClick={() => setQuery(q)}
              className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white rounded-full transition-colors"
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
        className="w-full mt-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Extracting Knowledge Graph...
          </>
        ) : (
          <>
            <Zap className="w-5 h-5" />
            Extract Knowledge Graph
          </>
        )}
      </button>
    </div>
  );
};

// Agent Card Component
const AgentCard = ({ agent }) => (
  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex flex-col items-center text-center hover:border-gray-600 transition-colors animate-fade-in">
    <span className="text-4xl mb-2">{agent.avatar_emoji}</span>
    <h4 className="text-sm font-bold text-white truncate w-full">{agent.name}</h4>
    <p className="text-xs text-gray-400 truncate w-full mb-2">{agent.occupation}</p>
    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${PERSONALITY_COLORS[agent.personality_type] || "badge-neutral"}`}>
      {agent.personality_type}
    </span>
    <div className="mt-2 flex items-center gap-1 text-xs text-gray-500">
      <Target className="w-3 h-3" />
      <span>Influence: {agent.influence_level}/10</span>
    </div>
  </div>
);

// Agent Step Component
const AgentStep = ({ sessionId, graph, onComplete }) => {
  const [numAgents, setNumAgents] = useState(20);
  const [loading, setLoading] = useState(false);
  const [agents, setAgents] = useState(null);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API}/sessions/${sessionId}/generate-agents`, {
        num_agents: numAgents,
      });
      setAgents(response.data.agents);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate agents");
    } finally {
      setLoading(false);
    }
  };

  // Count personalities
  const personalityCounts = agents?.reduce((acc, agent) => {
    acc[agent.personality_type] = (acc[agent.personality_type] || 0) + 1;
    return acc;
  }, {});

  if (agents) {
    return (
      <div className="animate-fade-in">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">
            {agents.length} Agents Generated
          </h2>
          <p className="text-gray-400">Ready to simulate social dynamics</p>
        </div>

        {/* Personality Distribution */}
        <div className="flex flex-wrap justify-center gap-2 mb-6">
          {Object.entries(personalityCounts || {}).map(([type, count]) => (
            <span key={type} className={`text-xs px-3 py-1 rounded-full border ${PERSONALITY_COLORS[type] || "badge-neutral"}`}>
              {type}: {count}
            </span>
          ))}
        </div>

        {/* Agent Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-6 max-h-[500px] overflow-y-auto p-2">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>

        <button
          data-testid="start-simulation-button"
          onClick={() => onComplete(agents)}
          className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
        >
          Start Simulation →
          <Play className="w-5 h-5" />
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Generate AI Agents</h2>
        <p className="text-gray-400">Create diverse personas based on your knowledge graph</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-400">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Context Summary */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">World Context</h3>
        <p className="text-gray-300">{graph?.summary}</p>
      </div>

      {/* Agent Count Slider */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <label className="text-sm font-medium text-gray-300">Number of Agents</label>
          <span className="text-2xl font-bold text-blue-400 mono">{numAgents}</span>
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
        <div className="flex justify-between text-xs text-gray-500 mt-2">
          <span>10</span>
          <span>30</span>
          <span>50</span>
        </div>
        <p className="text-xs text-gray-500 mt-3">
          Estimated generation time: ~{Math.ceil(numAgents / 10) * 15} seconds
        </p>
      </div>

      <button
        data-testid="generate-agents-button"
        onClick={handleGenerate}
        disabled={loading}
        className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating {numAgents} Agents...
          </>
        ) : (
          <>
            <Users className="w-5 h-5" />
            Generate Agents
          </>
        )}
      </button>
    </div>
  );
};

// Post Card Component
const PostCard = ({ post, isReply }) => (
  <div
    className={`p-4 border border-gray-800 rounded-lg bg-gray-950/50 hover:bg-gray-800/50 transition-colors animate-slide-up ${
      isReply ? "ml-6 border-l-2 border-l-blue-500" : ""
    } ${post.platform === "Reddit" ? "border-l-2 border-l-orange-500" : ""}`}
  >
    <div className="flex items-start gap-3">
      <span className="text-2xl">{post.agent_emoji}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-white text-sm">{post.agent_name}</span>
          <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">R{post.round}</span>
          {isReply && (
            <span className="text-xs text-blue-400">↩ reply to {post.reply_to}</span>
          )}
        </div>
        <p className="text-gray-300 text-sm">{post.content}</p>
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
  const twitterFeedRef = useRef(null);
  const redditFeedRef = useRef(null);

  const startSimulation = async () => {
    setSimulating(true);
    setError(null);
    try {
      await axios.post(`${API}/sessions/${sessionId}/simulate`, { num_rounds: numRounds });
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start simulation");
      setSimulating(false);
    }
  };

  // Poll for status and posts
  useEffect(() => {
    if (!simulating) return;

    const interval = setInterval(async () => {
      try {
        const [statusRes, postsRes] = await Promise.all([
          axios.get(`${API}/sessions/${sessionId}/simulation-status`),
          axios.get(`${API}/sessions/${sessionId}/posts`),
        ]);
        setStatus(statusRes.data);
        setPosts(postsRes.data.posts);

        if (statusRes.data.status === "simulation_done") {
          clearInterval(interval);
        } else if (statusRes.data.status === "error") {
          setError("Simulation encountered an error");
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [simulating, sessionId]);

  // Auto-scroll feeds
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
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-white mb-2">Run Simulation</h2>
          <p className="text-gray-400">Watch {agents?.length || 0} agents debate and discuss</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <label className="text-sm font-medium text-gray-300">Number of Rounds</label>
            <span className="text-2xl font-bold text-blue-400 mono">{numRounds}</span>
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
          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span>3 rounds</span>
            <span>9 rounds</span>
            <span>15 rounds</span>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            Estimated time: ~{numRounds * 30} seconds
          </p>
        </div>

        <button
          data-testid="run-simulation-button"
          onClick={startSimulation}
          className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
        >
          <Play className="w-5 h-5" />
          🚀 Start Simulation
        </button>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">
            {isDone ? "Simulation Complete" : `Round ${status?.current_round || 0} of ${status?.total_rounds || numRounds}`}
          </span>
          <span className="text-sm text-blue-400 mono">{posts.length} posts</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-500"
            style={{ width: `${((status?.current_round || 0) / (status?.total_rounds || numRounds)) * 100}%` }}
          />
        </div>
      </div>

      {/* Dual Feed Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Twitter Feed */}
        <div className="flex flex-col h-[600px] border border-gray-800 rounded-xl bg-gray-900 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between bg-gray-950">
            <div className="flex items-center gap-2">
              <Twitter className="w-5 h-5 text-blue-400" />
              <span className="font-semibold text-white">Twitter Feed</span>
            </div>
            <span className="text-xs text-gray-500">{twitterPosts.length} posts</span>
          </div>
          <div ref={twitterFeedRef} className="flex-1 overflow-y-auto p-4 space-y-3">
            {twitterPosts.map((post, i) => (
              <PostCard key={i} post={post} isReply={post.post_type === "reply"} />
            ))}
            {!isDone && twitterPosts.length === 0 && (
              <div className="flex items-center justify-center h-full text-gray-500">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                Waiting for posts...
              </div>
            )}
          </div>
        </div>

        {/* Reddit Feed */}
        <div className="flex flex-col h-[600px] border border-gray-800 rounded-xl bg-gray-900 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between bg-gray-950">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-orange-500 flex items-center justify-center text-white text-xs font-bold">R</div>
              <span className="font-semibold text-white">Reddit Feed</span>
            </div>
            <span className="text-xs text-gray-500">{redditPosts.length} posts</span>
          </div>
          <div ref={redditFeedRef} className="flex-1 overflow-y-auto p-4 space-y-3">
            {redditPosts.map((post, i) => (
              <PostCard key={i} post={post} isReply={post.post_type === "reply"} />
            ))}
            {!isDone && redditPosts.length === 0 && (
              <div className="flex items-center justify-center h-full text-gray-500">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                Waiting for posts...
              </div>
            )}
          </div>
        </div>
      </div>

      {isDone && (
        <button
          data-testid="generate-report-button"
          onClick={() => onComplete(posts)}
          className="w-full mt-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
        >
          Generate Report →
          <BarChart3 className="w-5 h-5" />
        </button>
      )}
    </div>
  );
};

// Confidence Badge Component
const ConfidenceBadge = ({ confidence, score }) => {
  const color = confidence === "High" ? "emerald" : confidence === "Medium" ? "amber" : "red";
  return (
    <div className="flex items-center gap-4">
      <div className={`relative w-24 h-24 rounded-full border-4 border-${color}-500/30 flex items-center justify-center`}>
        <div className={`text-2xl font-bold text-${color}-400 mono`}>{Math.round(score * 100)}%</div>
        <svg className="absolute inset-0 w-full h-full -rotate-90">
          <circle
            cx="48"
            cy="48"
            r="44"
            fill="none"
            stroke={color === "emerald" ? "#10b981" : color === "amber" ? "#f59e0b" : "#ef4444"}
            strokeWidth="4"
            strokeDasharray={`${score * 276} 276`}
            className="transition-all duration-1000"
          />
        </svg>
      </div>
      <div>
        <span className={`text-lg font-bold text-${color}-400`}>{confidence} Confidence</span>
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
      <div className="max-w-2xl mx-auto text-center">
        <h2 className="text-3xl font-bold text-white mb-4">Generate Prediction Report</h2>
        <p className="text-gray-400 mb-6">
          Analyze {posts?.length || 0} posts from the simulation to produce insights
        </p>
        
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          data-testid="analyze-report-button"
          onClick={generateReport}
          className="py-3 px-8 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 mx-auto transition-colors"
        >
          <BarChart3 className="w-5 h-5" />
          🔍 Generate Report
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="animate-pulse-glow inline-block p-6 rounded-full bg-blue-500/10 mb-6">
          <Loader2 className="w-12 h-12 text-blue-400 animate-spin" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">ReportAgent Analyzing...</h2>
        <p className="text-gray-400">Processing simulation data and generating insights</p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in space-y-6">
      {/* Prediction Card */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Predicted Outcome</h3>
            <p className="text-2xl font-bold text-white mb-2">{report.prediction?.outcome}</p>
            <p className="text-sm text-gray-400">Timeframe: {report.prediction?.timeframe}</p>
          </div>
          <ConfidenceBadge 
            confidence={report.prediction?.confidence} 
            score={report.prediction?.confidence_score || 0.5} 
          />
        </div>
      </div>

      {/* Executive Summary */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-3">Executive Summary</h3>
        <p className="text-gray-300 leading-relaxed">{report.executive_summary}</p>
      </div>

      {/* Opinion Landscape */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">Opinion Landscape</h3>
        
        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1">
            <div className="flex h-4 rounded-full overflow-hidden">
              <div 
                className="bg-emerald-500" 
                style={{ width: `${report.opinion_landscape?.support_percentage || 0}%` }}
              />
              <div 
                className="bg-red-500" 
                style={{ width: `${report.opinion_landscape?.opposition_percentage || 0}%` }}
              />
              <div 
                className="bg-gray-600" 
                style={{ width: `${report.opinion_landscape?.undecided_percentage || 0}%` }}
              />
            </div>
            <div className="flex justify-between text-xs mt-2">
              <span className="text-emerald-400">Support: {report.opinion_landscape?.support_percentage}%</span>
              <span className="text-red-400">Opposition: {report.opinion_landscape?.opposition_percentage}%</span>
              <span className="text-gray-400">Undecided: {report.opinion_landscape?.undecided_percentage}%</span>
            </div>
          </div>
        </div>

        {/* Factions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {report.opinion_landscape?.key_factions?.map((faction, i) => (
            <div key={i} className="p-4 bg-gray-950 rounded-lg border border-gray-800">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-white">{faction.name}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  faction.size === "Large" ? "bg-blue-500/20 text-blue-400" :
                  faction.size === "Medium" ? "bg-amber-500/20 text-amber-400" :
                  "bg-gray-500/20 text-gray-400"
                }`}>
                  {faction.size}
                </span>
              </div>
              <p className="text-sm text-gray-400 mb-2">{faction.stance}</p>
              <div className="flex flex-wrap gap-1">
                {faction.key_arguments?.map((arg, j) => (
                  <span key={j} className="text-xs px-2 py-0.5 bg-gray-800 text-gray-300 rounded">
                    {arg}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Key Turning Points */}
      {report.key_turning_points?.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Key Turning Points</h3>
          <div className="space-y-4">
            {report.key_turning_points.map((point, i) => (
              <div key={i} className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold text-sm">
                  R{point.round}
                </div>
                <div>
                  <p className="text-white font-medium">{point.description}</p>
                  <p className="text-sm text-gray-400">{point.impact}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Factors */}
      {report.risk_factors?.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            Risk Factors
          </h3>
          <div className="space-y-3">
            {report.risk_factors.map((risk, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded bg-red-500/5 border border-red-500/10">
                <span className={`text-xs px-2 py-0.5 rounded ${
                  risk.likelihood === "High" ? "bg-red-500/20 text-red-400" :
                  risk.likelihood === "Medium" ? "bg-amber-500/20 text-amber-400" :
                  "bg-gray-500/20 text-gray-400"
                }`}>
                  {risk.likelihood}
                </span>
                <div>
                  <p className="text-white font-medium">{risk.factor}</p>
                  <p className="text-sm text-gray-400">{risk.impact}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Agent Highlights */}
      {report.agent_highlights?.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Agent Highlights</h3>
          <div className="space-y-4">
            {report.agent_highlights.map((highlight, i) => (
              <div key={i} className="p-4 bg-gray-950 rounded-lg border border-gray-800">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-semibold text-white">{highlight.agent_name}</span>
                </div>
                <p className="text-sm text-gray-400 mb-2">{highlight.role_in_simulation}</p>
                <blockquote className="text-sm text-blue-300 italic border-l-2 border-blue-500 pl-3">
                  "{highlight.notable_quote}"
                </blockquote>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        data-testid="interact-with-agents-button"
        onClick={() => onComplete(report)}
        className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
      >
        💬 Interact with Agents →
        <ChevronRight className="w-5 h-5" />
      </button>
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

  // Load chat history when target changes
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await axios.get(
          `${API}/sessions/${sessionId}/chat-history?target_type=${selectedTarget.type}&target_id=${selectedTarget.id}`
        );
        setMessages(response.data.history || []);
      } catch (err) {
        console.error("Failed to load chat history:", err);
        setMessages([]);
      }
    };
    loadHistory();
  }, [sessionId, selectedTarget]);

  // Auto-scroll to bottom
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

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickPrompts = selectedTarget.type === "report"
    ? ["What's the most important finding?", "What are the biggest risks?", "How confident should I be?"]
    : ["What's your take on this?", "Why do you feel that way?", "What would change your mind?"];

  return (
    <div className="flex h-[700px] border border-gray-800 rounded-xl overflow-hidden bg-gray-900">
      {/* Sidebar */}
      <div className="w-64 border-r border-gray-800 bg-gray-950 overflow-y-auto hidden md:block">
        <div className="p-4 border-b border-gray-800">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Chat Targets</h3>
        </div>
        
        {/* ReportAgent */}
        <button
          data-testid="chat-target-report-agent"
          onClick={() => setSelectedTarget({ type: "report", id: "report_agent", name: "ReportAgent" })}
          className={`w-full p-4 flex items-center gap-3 border-b border-gray-800 transition-colors ${
            selectedTarget.id === "report_agent" ? "bg-blue-500/10 border-l-2 border-l-blue-500" : "hover:bg-gray-900"
          }`}
        >
          <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center text-xl">
            🧠
          </div>
          <div className="text-left">
            <p className="font-semibold text-white text-sm">ReportAgent</p>
            <p className="text-xs text-gray-500">Analysis Expert</p>
          </div>
        </button>

        {/* Agents */}
        <div className="p-2">
          <p className="text-xs text-gray-500 px-2 py-1">Simulation Agents</p>
        </div>
        {agents?.map((agent) => (
          <button
            key={agent.id}
            data-testid={`chat-target-${agent.id}`}
            onClick={() => setSelectedTarget({ type: "agent", id: agent.id, name: agent.name, agent })}
            className={`w-full p-3 flex items-center gap-3 border-b border-gray-800/50 transition-colors ${
              selectedTarget.id === agent.id ? "bg-blue-500/10 border-l-2 border-l-blue-500" : "hover:bg-gray-900"
            }`}
          >
            <span className="text-2xl">{agent.avatar_emoji}</span>
            <div className="text-left min-w-0">
              <p className="font-medium text-white text-sm truncate">{agent.name}</p>
              <p className="text-xs text-gray-500 truncate">{agent.occupation}</p>
            </div>
          </button>
        ))}
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="px-6 py-4 border-b border-gray-800 bg-gray-950 flex items-center gap-3">
          <span className="text-2xl">
            {selectedTarget.type === "report" ? "🧠" : selectedTarget.agent?.avatar_emoji}
          </span>
          <div>
            <h3 className="font-semibold text-white">{selectedTarget.name}</h3>
            <p className="text-xs text-gray-500">
              {selectedTarget.type === "report" 
                ? "Analysis Expert" 
                : selectedTarget.agent?.occupation}
            </p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              <p className="mb-4">Start a conversation with {selectedTarget.name}</p>
              <div className="flex flex-wrap justify-center gap-2">
                {quickPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(prompt)}
                    className="text-sm px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-full transition-colors"
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
                className={`max-w-[80%] px-4 py-2 rounded-2xl ${
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
              <div className="bg-gray-800 text-gray-200 px-4 py-2 rounded-2xl rounded-tl-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-800 bg-gray-950">
          <div className="flex gap-3">
            <input
              data-testid="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Message ${selectedTarget.name}...`}
              className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
            <button
              data-testid="send-message-button"
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            >
              <Send className="w-5 h-5" />
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

  // Create session on mount
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
          <Loader2 className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Initializing SwarmSim...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center text-red-400">
          <AlertCircle className="w-12 h-12 mx-auto mb-4" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <StepIndicator
          currentStep={currentStep}
          completedSteps={completedSteps}
          onStepClick={handleStepClick}
        />

        <div className="mt-8">
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
