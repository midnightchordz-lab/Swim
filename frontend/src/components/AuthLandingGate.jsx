import React, { useState } from "react";
import { ArrowRight, BarChart3, Database, Lock, Shield, Sparkles, Zap } from "lucide-react";
import ParticleBackground from "./ParticleBackground";

const features = [
  {
    icon: <Database className="w-4 h-4" />,
    title: "Evidence Ledger",
    text: "Trace every prediction back to sources, freshness, confidence impact, and usage.",
  },
  {
    icon: <BarChart3 className="w-4 h-4" />,
    title: "Ensemble Forecasts",
    text: "Bootstrap the simulated world into consensus, variance, and stability signals.",
  },
  {
    icon: <Zap className="w-4 h-4" />,
    title: "God-View Injection",
    text: "Inject shocks after a run and watch agents recalibrate the simulated future.",
  },
  {
    icon: <Shield className="w-4 h-4" />,
    title: "Calibrated Confidence",
    text: "Show raw vs adjusted confidence, uncertainty bands, caveats, and evidence strength.",
  },
];

const steps = [
  "Ask a prediction question",
  "Build graph + agent society",
  "Run the swarm simulation",
  "Audit evidence + ensemble stability",
  "Interrogate agents and ReportAgent",
];

const AuthLandingGate = ({ onSignIn }) => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("signin");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    const trimmedEmail = email.trim();
    if (!trimmedEmail || !trimmedEmail.includes("@")) {
      setError("Enter a valid email to continue.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await onSignIn({
        mode,
        name: name.trim() || trimmedEmail.split("@")[0],
        email: trimmedEmail,
        password,
      });
    } catch (err) {
      setError(err.response?.data?.detail || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", position: "relative", overflow: "hidden" }}>
      <canvas id="bg-canvas" />
      <div className="grid-overlay" />
      <ParticleBackground />
      <div className="relative z-10 min-h-screen flex flex-col">
        <header className="app-header">
          <div className="logo-wrap">
            <div className="logo-icon-box">
              <Sparkles className="w-4 h-4 text-sw-cyan" />
            </div>
            <div>
              <div className="logo-name">Predicta</div>
              <div className="logo-tagline">Evidence-Aware Prediction Lab</div>
            </div>
          </div>
          <span className="badge-live">Private Beta</span>
        </header>

        <main className="flex-1 w-full max-w-7xl mx-auto px-4 py-10 md:py-16">
          <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-8 items-center">
            <section className="space-y-7">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs mono" style={{ background: "var(--cyan-dim)", color: "var(--cyan)", border: "1px solid var(--border-bright)" }}>
                <Lock className="w-3.5 h-3.5" />
                SIGN IN TO ACCESS THE PREDICTION LAB
              </div>
              <div>
                <h1 className="text-5xl md:text-7xl font-extrabold leading-tight mb-5" style={{ fontFamily: "var(--display)", color: "var(--text)" }}>
                  Predict Anything.
                  <br />
                  <span className="text-sw-cyan">Know Why.</span>
                </h1>
                <p className="text-lg md:text-xl max-w-3xl" style={{ color: "var(--text2)", lineHeight: 1.7 }}>
                  A decision-grade swarm intelligence lab with live data grounding, agent societies, shock injection, ensemble forecasts, and a transparent evidence ledger.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {features.map((feature) => (
                  <div key={feature.title} className="rounded-xl border border-sw bg-panel p-4">
                    <div className="flex items-center gap-2 mb-2 text-sw-cyan">
                      {feature.icon}
                      <h3 className="text-sm font-bold text-sw">{feature.title}</h3>
                    </div>
                    <p className="text-xs text-sw2 leading-relaxed">{feature.text}</p>
                  </div>
                ))}
              </div>

              <div className="rounded-2xl border border-sw bg-panel p-4">
                <p className="text-xs uppercase tracking-wider text-sw3 mb-3">Workflow</p>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
                  {steps.map((step, index) => (
                    <div key={step} className="rounded-lg bg-sw3/50 border border-sw p-3">
                      <p className="mono text-[10px] text-sw-cyan mb-1">{String(index + 1).padStart(2, "0")}</p>
                      <p className="text-xs text-sw2">{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="rounded-2xl border border-sw bg-panel p-5 md:p-6 shadow-[0_0_60px_rgba(0,245,196,0.08)]">
              <div className="mb-5">
                <p className="text-xs uppercase tracking-wider text-sw3 mb-2">Secure access</p>
                <h2 className="text-2xl font-bold text-sw mb-2">{mode === "signin" ? "Sign in to start predicting" : "Create your analyst account"}</h2>
                <p className="text-sm text-sw2">
                  Server-side accounts protect simulation sessions, reports, and agent chats behind a signed JWT.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 mb-4">
                {["signin", "signup"].map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => { setMode(item); setError(""); }}
                    className={`rounded-lg px-3 py-2 text-xs font-semibold border transition-colors ${
                      mode === item ? "border-sw-cyan bg-sw-cyan/10 text-sw-cyan" : "border-sw text-sw2"
                    }`}
                  >
                    {item === "signin" ? "Sign In" : "Sign Up"}
                  </button>
                ))}
              </div>

              <form onSubmit={submit} className="space-y-4">
                {mode === "signup" && (
                  <div>
                    <label className="text-xs text-sw2 mb-1 block">Name</label>
                    <input
                      className="field"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      placeholder="Analyst name"
                    />
                  </div>
                )}
                <div>
                  <label className="text-xs text-sw2 mb-1 block">Email</label>
                  <input
                    data-testid="signin-email"
                    className="field"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                  />
                </div>
                <div>
                  <label className="text-xs text-sw2 mb-1 block">Password</label>
                  <input
                    data-testid="signin-password"
                    className="field"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="At least 8 characters"
                  />
                </div>
                {error && <p className="text-xs text-red-400">{error}</p>}
                <button data-testid="signin-button" className="btn-primary" type="submit" disabled={loading}>
                  {loading ? "Authenticating..." : mode === "signin" ? "Enter Predicta" : "Create Account"}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>

              <div className="mt-5 rounded-xl bg-sw3/40 border border-sw p-3">
                <p className="text-[10px] uppercase tracking-wider text-sw3 mb-1">Why this beats generic swarm demos</p>
                <p className="text-xs text-sw2 leading-relaxed">
                  Predicta does not stop at a simulated answer. It shows source grounding, uncertainty, ensemble stability, and how the world changes when you inject new events.
                </p>
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
};

export default AuthLandingGate;
