const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export interface User {
  username: string;
  email: string;
  role: "OPS" | "FINANCE" | "COMPLIANCE" | "ADMIN";
  disabled: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export class AuthService {
  private static readonly TOKEN_KEY = "auth_token";
  private static readonly USER_KEY = "auth_user";

  static async login(username: string, password: string): Promise<TokenResponse> {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });

    if (!res.ok) {
      if (res.status === 401) {
        throw new Error("Invalid username or password");
      }
      throw new Error(`Login failed: ${res.statusText}`);
    }

    const data: TokenResponse = await res.json();
    if (isBrowser()) {
      localStorage.setItem(this.TOKEN_KEY, data.access_token);
    }
    return data;
  }

  static getToken(): string | null {
    if (!isBrowser()) return null;
    return localStorage.getItem(this.TOKEN_KEY);
  }

  static async getCurrentUser(): Promise<User> {
    const token = this.getToken();
    if (!token) {
      throw new Error("Not authenticated");
    }

    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) {
      if (res.status === 401) {
        this.logout();
        throw new Error("Session expired");
      }
      throw new Error(`Failed to get user: ${res.statusText}`);
    }

    const user: User = await res.json();
    if (isBrowser()) {
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }
    return user;
  }

  static logout(): void {
    if (!isBrowser()) return;
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  static isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  static getCachedUser(): User | null {
    if (!isBrowser()) return null;
    const userStr = localStorage.getItem(this.USER_KEY);
    if (!userStr) return null;
    try {
      return JSON.parse(userStr) as User;
    } catch {
      return null;
    }
  }

  static hasRole(role: User["role"]): boolean {
    const user = this.getCachedUser();
    return user?.role === role;
  }

  static hasAnyRole(roles: User["role"][]): boolean {
    const user = this.getCachedUser();
    return user ? roles.includes(user.role) : false;
  }
}
