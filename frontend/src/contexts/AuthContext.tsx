import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from "react";
import { fetchMe, login } from "../services/auth";
import { ApiError } from "../services/api";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("vendifacil:token");
    if (!token) {
      setLoading(false);
      return;
    }

    fetchMe()
      .then((currentUser) => {
        localStorage.setItem("vendifacil:offline-user", JSON.stringify(currentUser));
        setUser(currentUser);
      })
      .catch((error) => {
        if (error instanceof ApiError && error.response.status === 0) {
          try {
            const cached = JSON.parse(localStorage.getItem("vendifacil:offline-user") ?? "null") as User | null;
            if (cached?.id && cached.account_id) setUser(cached);
          } catch { localStorage.removeItem("vendifacil:offline-user"); }
          return;
        }
        localStorage.removeItem("vendifacil:token");
        localStorage.removeItem("vendifacil:offline-user");
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      signIn: async (email: string, password: string) => {
        const { access_token } = await login(email, password);
        localStorage.setItem("vendifacil:token", access_token);
        const currentUser = await fetchMe();
        localStorage.setItem("vendifacil:offline-user", JSON.stringify(currentUser));
        setUser(currentUser);
      },
      signOut: () => {
        localStorage.removeItem("vendifacil:token");
        localStorage.removeItem("vendifacil:offline-user");
        setUser(null);
      },
    }),
    [loading, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth precisa estar dentro de AuthProvider");
  return context;
}
