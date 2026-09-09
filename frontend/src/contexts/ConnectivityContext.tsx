import { createContext, useContext, useEffect, useRef, useState, type PropsWithChildren } from "react";
import { useAuth } from "./AuthContext";
import { allOperations } from "../services/offlineDb";
import { backendAvailable, synchronizeQueue } from "../services/synchronization";

export type ConnectionStatus = "ONLINE" | "OFFLINE" | "SYNCING" | "SYNC_ERROR";
interface ConnectivityValue { status: ConnectionStatus; pending: number; attention: number; lastSync?: string; checkNow: () => Promise<void>; }
const ConnectivityContext = createContext<ConnectivityValue | null>(null);

export function ConnectivityProvider({ children }: PropsWithChildren) {
  const { user } = useAuth();
  const [status, setStatus] = useState<ConnectionStatus>("ONLINE");
  const [pending, setPending] = useState(0);
  const [attention, setAttention] = useState(0);
  const [lastSync, setLastSync] = useState<string>();
  const syncing = useRef(false);

  async function refreshCounts() {
    if (!user) { setPending(0); setAttention(0); return; }
    const items = (await allOperations()).filter(item => item.account_id === user.account_id && item.user_id === user.id);
    setPending(items.filter(item => item.status !== "ATTENTION").length);
    setAttention(items.filter(item => item.status === "ATTENTION").length);
  }

  async function checkNow() {
    const available = await backendAvailable();
    if (!available) { setStatus("OFFLINE"); await refreshCounts(); return; }
    if (!user || syncing.current) { setStatus("ONLINE"); await refreshCounts(); return; }
    syncing.current = true; setStatus("SYNCING");
    try {
      await synchronizeQueue(user.account_id, user.id);
      setLastSync(new Date().toISOString());
      await refreshCounts();
      const remaining = (await allOperations()).filter(item => item.account_id === user.account_id && item.user_id === user.id && item.status !== "ATTENTION").length;
      setStatus(remaining ? "SYNC_ERROR" : "ONLINE");
    } catch { setStatus("SYNC_ERROR"); }
    finally { syncing.current = false; }
  }

  useEffect(() => {
    void checkNow();
    const handleOnline = () => void checkNow();
    const handleOffline = () => setStatus("OFFLINE");
    window.addEventListener("online", handleOnline); window.addEventListener("offline", handleOffline);
    const timer = window.setInterval(() => void checkNow(), 30000);
    return () => { window.removeEventListener("online", handleOnline); window.removeEventListener("offline", handleOffline); window.clearInterval(timer); };
  }, [user?.id]);

  return <ConnectivityContext.Provider value={{ status, pending, attention, lastSync, checkNow }}>{children}</ConnectivityContext.Provider>;
}

export function useConnectivity() {
  const value = useContext(ConnectivityContext);
  if (!value) throw new Error("useConnectivity precisa estar dentro de ConnectivityProvider");
  return value;
}
