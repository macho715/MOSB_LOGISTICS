import { useState, type FormEvent } from "react";
import { AuthService } from "../lib/auth";

interface LoginProps {
  onLoginSuccess: () => void;
}

export function Login({ onLoginSuccess }: LoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await AuthService.login(username, password);
      await AuthService.getCurrentUser();
      onLoginSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 420,
        margin: "60px auto",
        padding: 24,
        borderRadius: 16,
        background: "rgba(10, 16, 24, 0.92)",
        border: "1px solid rgba(255,255,255,0.08)",
      }}
    >
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>
        MOSB Logistics Dashboard
      </div>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: "block", marginBottom: 6, opacity: 0.8 }}>
            Username
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={{
              width: "100%",
              padding: 10,
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.04)",
              color: "#e6edf3",
            }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: "block", marginBottom: 6, opacity: 0.8 }}>
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{
              width: "100%",
              padding: 10,
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.04)",
              color: "#e6edf3",
            }}
          />
        </div>
        {error && (
          <div style={{ color: "#ff6b6b", marginBottom: 10 }}>{error}</div>
        )}
        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: 10,
            borderRadius: 10,
            border: "1px solid rgba(255,255,255,0.12)",
            background: "rgba(255,255,255,0.08)",
            color: "#e6edf3",
            fontWeight: 600,
          }}
        >
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
      <div style={{ marginTop: 16, fontSize: 12, opacity: 0.7 }}>
        <div>Demo users:</div>
        <ul style={{ margin: "8px 0 0 16px" }}>
          <li>ops_user / ops123 (OPS)</li>
          <li>finance_user / finance123 (FINANCE)</li>
          <li>compliance_user / compliance123 (COMPLIANCE)</li>
          <li>admin / admin123 (ADMIN)</li>
        </ul>
      </div>
    </div>
  );
}
