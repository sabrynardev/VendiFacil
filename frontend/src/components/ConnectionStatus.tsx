import { AlertTriangle, Cloud, CloudOff, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";
import { useConnectivity } from "../contexts/ConnectivityContext";

export function ConnectionStatus() {
  const { status, pending, attention } = useConnectivity();
  const offline = status === "OFFLINE";
  const syncing = status === "SYNCING";
  return <Link to="/synchronization" className={`fixed bottom-4 right-4 z-40 flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-medium shadow-soft ${offline || attention ? "border-amber-200 bg-amber-50 text-amber-800" : "border-stroke bg-white/95 text-brandDark"}`}>
    {offline ? <CloudOff size={15}/> : syncing ? <RefreshCw className="animate-spin" size={15}/> : attention ? <AlertTriangle size={15}/> : <Cloud size={15}/>}
    {offline ? `Offline${pending ? ` · ${pending} pendente(s)` : ""}` : syncing ? "Sincronizando" : attention ? `${attention} requer atenção` : pending ? `${pending} aguardando` : "Online"}
  </Link>;
}
