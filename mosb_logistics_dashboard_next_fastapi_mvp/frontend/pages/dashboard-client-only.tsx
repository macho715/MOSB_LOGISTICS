import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { Login } from "../components/Login";
import { AuthService, User } from "../lib/auth";

const ClientOnlyDashboard = dynamic(
  () => import("../components/client-only/ClientOnlyDashboard"),
  { ssr: false },
);

export default function DashboardClientOnlyPage() {
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const initAuth = async () => {
      if (!AuthService.isAuthenticated()) {
        if (active) setAuthReady(true);
        return;
      }
      try {
        const me = await AuthService.getCurrentUser();
        if (!active) return;
        setUser(me);
      } catch {
        if (!active) return;
        setUser(null);
        setAuthError("Authentication failed");
      }
      if (active) setAuthReady(true);
    };

    initAuth();

    return () => {
      active = false;
    };
  }, []);

  const handleLoginSuccess = () => {
    const cached = AuthService.getCachedUser();
    if (cached) {
      setUser(cached);
      setAuthError(null);
    } else {
      setAuthError("Login succeeded but user cache missing");
    }
  };

  const handleLogout = () => {
    AuthService.logout();
    setUser(null);
    setAuthError(null);
  };

  if (!authReady) {
    return (
      <div style={{ padding: 16 }}>
        <div className="small">Authenticating...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div style={{ padding: 16 }}>
        {authError && (
          <div style={{ color: "#ff6b6b", marginBottom: 12 }}>{authError}</div>
        )}
        <Login onLoginSuccess={handleLoginSuccess} />
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          padding: 8,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid rgba(255,255,255,0.12)",
        }}
      >
        <div>
          <b>MOSB Logistics Dashboard</b> - Client-Only Mode
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <span className="small">
            User: {user.username} ({user.role})
          </span>
          <button
            onClick={handleLogout}
            style={{
              padding: "4px 12px",
              borderRadius: 6,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.06)",
              color: "#e6edf3",
            }}
          >
            Logout
          </button>
        </div>
      </div>
      <ClientOnlyDashboard />
    </div>
  );
}
