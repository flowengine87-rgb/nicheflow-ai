import { useState, useEffect, useRef, useCallback } from "react";

const SUPABASE_URL = "https://gfulpvqqpakcgubkilwc.supabase.co";
const SUPABASE_KEY = "sb_publishable_U9zJp_BBd-jkJCwvGimNmw_E4NyynFN";
const API_URL = "https://web-production-1f143.up.railway.app";

async function supaAuth(action, email, password) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/${action}`, {
    method: "POST",
    headers: { apikey: SUPABASE_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error_description || data.msg || "Auth error");
  return data;
}

function estimateTokens(text) { return Math.ceil(text.length / 4); }

export default function NicheFlowAI() {
  const [view, setView] = useState("landing");
  const [user, setUser] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem("nicheflow_user");
    if (stored) { try { const u = JSON.parse(stored); setUser(u); setView("app"); } catch {} }
  }, []);

  function handleAuthSuccess(userData) {
    localStorage.setItem("nicheflow_user", JSON.stringify(userData));
    setUser(userData); setView("app");
  }

  function handleLogout() {
    localStorage.removeItem("nicheflow_user");
    setUser(null); setView("landing");
  }

  if (view === "app" && user) return <AppShell user={user} onLogout={handleLogout} />;
  if (view === "login" || view === "signup") return <AuthPage mode={view} onSuccess={handleAuthSuccess} onSwitch={setView} onBack={() => setView("landing")} />;
  return <LandingPage onLogin={() => setView("login")} onSignup={() => setView("signup")} />;
}

// Placeholder components - will be replaced with full code
function LandingPage({ onLogin, onSignup }) {
  return (
    <div style={{ minHeight: "100vh", background: "#08090d", color: "#f0f1f5", fontFamily: "sans-serif", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
      <h1 style={{ fontSize: 48, fontWeight: 800, marginBottom: 16 }}>NicheFlow AI</h1>
      <p style={{ color: "#9ba3b8", marginBottom: 32 }}>AI-powered content automation for niche sites</p>
      <div style={{ display: "flex", gap: 12 }}>
        <button onClick={onSignup} style={{ padding: "12px 28px", background: "#6366f1", color: "#fff", border: "none", borderRadius: 10, cursor: "pointer", fontSize: 15 }}>Get Started Free</button>
        <button onClick={onLogin} style={{ padding: "12px 28px", background: "transparent", color: "#9ba3b8", border: "1px solid #2a2f40", borderRadius: 10, cursor: "pointer", fontSize: 15 }}>Sign In</button>
      </div>
    </div>
  );
}

function AuthPage({ mode, onSuccess, onSwitch, onBack }) {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false); const [error, setError] = useState(""); const [done, setDone] = useState(false);
  async function submit(e) {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const action = mode === "login" ? "token?grant_type=password" : "signup";
      const data = await supaAuth(action, email, password);
      if (mode === "signup") setDone(true); else onSuccess(data);
    } catch (err) { setError(err.message); } finally { setLoading(false); }
  }
  return (
    <div style={{ minHeight: "100vh", background: "#08090d", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 400, background: "#0e1018", border: "1px solid #1e2333", borderRadius: 20, padding: 40 }}>
        <button onClick={onBack} style={{ background: "none", border: "none", color: "#9ba3b8", cursor: "pointer", marginBottom: 20 }}>← Back</button>
        <h2 style={{ color: "#f0f1f5", marginBottom: 8 }}>{mode === "login" ? "Welcome back" : "Create account"}</h2>
        {done ? <p style={{ color: "#10b981" }}>✓ Check your email to confirm, then log in.</p> : (
          <form onSubmit={submit}>
            {error && <p style={{ color: "#ef4444", marginBottom: 12 }}>{error}</p>}
            <input style={{ width: "100%", padding: "10px 14px", background: "#141720", border: "1px solid #1e2333", borderRadius: 10, color: "#f0f1f5", marginBottom: 12, boxSizing: "border-box" }} type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" required />
            <input style={{ width: "100%", padding: "10px 14px", background: "#141720", border: "1px solid #1e2333", borderRadius: 10, color: "#f0f1f5", marginBottom: 16, boxSizing: "border-box" }} type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" required />
            <button style={{ width: "100%", padding: "12px", background: "#6366f1", color: "#fff", border: "none", borderRadius: 10, cursor: "pointer" }} disabled={loading}>{loading ? "..." : mode === "login" ? "Sign in →" : "Create account →"}</button>
            <p style={{ textAlign: "center", marginTop: 16, color: "#9ba3b8", fontSize: 14 }}>
              {mode === "login" ? "No account? " : "Have one? "}
              <span style={{ color: "#818cf8", cursor: "pointer" }} onClick={() => onSwitch(mode === "login" ? "signup" : "login")}>{mode === "login" ? "Sign up" : "Sign in"}</span>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}

function AppShell({ user, onLogout }) {
  const [page, setPage] = useState("dashboard");
  const email = user?.user?.email || user?.email || "user@nicheflow.ai";
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#08090d", color: "#f0f1f5", fontFamily: "sans-serif" }}>
      <aside style={{ width: 220, background: "#0e1018", borderRight: "1px solid #1e2333", padding: "20px 10px", display: "flex", flexDirection: "column" }}>
        <div style={{ fontWeight: 700, fontSize: 16, padding: "0 10px 20px", color: "#818cf8" }}>NicheFlow AI</div>
        {[["dashboard","◉","Dashboard"],["generate","⚡","Generate"],["history","📋","History"],["pinterest","📌","Pinterest"],["settings","⚙️","Settings"]].map(([id,icon,label]) => (
          <button key={id} onClick={() => setPage(id)} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 12px", borderRadius: 8, border: "none", background: page === id ? "rgba(99,102,241,0.15)" : "transparent", color: page === id ? "#818cf8" : "#9ba3b8", cursor: "pointer", fontSize: 14, marginBottom: 2 }}>
            {icon} {label}
          </button>
        ))}
        <div style={{ marginTop: "auto", padding: "10px 12px", fontSize: 12, color: "#5a6278", borderTop: "1px solid #1e2333", paddingTop: 16 }}>
          <div style={{ marginBottom: 8 }}>{email}</div>
          <button onClick={onLogout} style={{ background: "none", border: "none", color: "#9ba3b8", cursor: "pointer", fontSize: 13 }}>Sign out →</button>
        </div>
      </aside>
      <main style={{ flex: 1, padding: 32 }}>
        {page === "dashboard" && <div><h2>Dashboard</h2><p style={{ color: "#9ba3b8", marginTop: 8 }}>Welcome back! Your content hub is ready.</p></div>}
        {page === "generate" && <div><h2>Generate Articles</h2><p style={{ color: "#9ba3b8", marginTop: 8 }}>Paste titles and let AI do the rest.</p></div>}
        {page === "history" && <div><h2>History</h2><p style={{ color: "#9ba3b8", marginTop: 8 }}>Your published articles will appear here.</p></div>}
        {page === "pinterest" && <div><h2>Pinterest Bot</h2><p style={{ color: "#9ba3b8", marginTop: 8 }}>Auto-pin your articles. Pro feature.</p></div>}
        {page === "settings" && <div><h2>Settings</h2><p style={{ color: "#9ba3b8", marginTop: 8 }}>Configure your API keys and prompts.</p></div>}
      </main>
    </div>
  );
}