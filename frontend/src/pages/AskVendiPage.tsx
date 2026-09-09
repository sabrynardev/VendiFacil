import { MessageCircle, Send, ShieldCheck } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { PeriodFilter, periodDates } from "../components/PeriodFilter";
import { intelligenceService } from "../services/intelligence";
import type { AskVendiResponse } from "../types";

const suggestions = ["Quanto vendi hoje?", "Quanto lucrei este mês?", "O que preciso repor?", "Quais produtos estão parados?", "Quem está me devendo?", "Qual fornecedor aumentou os preços?"];
type Message = { role: "user" | "assistant"; text: string; meta?: AskVendiResponse };

export function AskVendiPage() {
  const initial = periodDates("30d");
  const [start, setStart] = useState(initial[0]);
  const [end, setEnd] = useState(initial[1]);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  async function submit(event?: FormEvent, suggested?: string) {
    event?.preventDefault();
    const text = (suggested ?? question).trim();
    if (!text || loading) return;
    setMessages(current => [...current, { role: "user", text }]); setQuestion(""); setLoading(true);
    try {
      const result = await intelligenceService.ask(text, start, end);
      setMessages(current => [...current, { role: "assistant", text: result.answer, meta: result }]);
    } catch (error) {
      setMessages(current => [...current, { role: "assistant", text: error instanceof Error ? error.message : "Não foi possível consultar o assistente agora. Os demais recursos continuam disponíveis." }]);
    } finally { setLoading(false); }
  }

  return <div className="space-y-6">
    <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end"><div><p className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-brand"><MessageCircle size={16}/> Consulta segura</p><h1 className="page-title mt-2">Pergunte ao Vendi</h1><p className="page-subtitle">Respostas curtas baseadas somente nos dados que seu perfil pode consultar.</p></div><PeriodFilter start={start} end={end} onChange={(from, to) => { setStart(from); setEnd(to); }}/></div>
    <div className="grid gap-6 xl:grid-cols-[0.7fr_1.3fr]"><Card><h2 className="font-semibold">Perguntas sugeridas</h2><div className="mt-4 space-y-2">{suggestions.map(item => <button key={item} className="w-full rounded-2xl border border-stroke bg-brand/4 p-3 text-left text-sm text-brandDark transition hover:bg-brand/8" onClick={() => void submit(undefined, item)}>{item}</button>)}</div><div className="mt-5 rounded-2xl bg-brand/5 p-4 text-sm text-slate-600"><p className="flex items-center gap-2 font-medium text-brandDeeper"><ShieldCheck size={17}/> Somente leitura</p><p className="mt-2 leading-5">O assistente não altera estoque, dívidas, preços, vendas ou caixa.</p></div></Card>
    <Card className="flex min-h-[560px] flex-col"><div className="flex-1 space-y-4 overflow-y-auto">{!messages.length && <div className="rounded-3xl bg-brand/5 p-6"><p className="font-medium text-brandDeeper">Como posso ajudar?</p><p className="mt-2 text-sm leading-6 text-slate-600">Pergunte sobre vendas, lucro, estoque, reposição, fiado, fornecedores, perdas ou validade. O período selecionado será informado na resposta.</p></div>}{messages.map((message, index) => <div key={index} className={`max-w-[88%] rounded-3xl p-4 text-sm leading-6 ${message.role === "user" ? "ml-auto bg-brand text-white" : "bg-brand/5 text-slate-700"}`}><p>{message.text}</p>{message.meta && <div className="mt-3 border-t border-brand/10 pt-3 text-xs text-slate-500"><p>Baseado em: {message.meta.sources.length ? message.meta.sources.join(", ") : "nenhuma consulta de dados"}.</p><p>Ferramenta: {message.meta.tool} · modo somente leitura.</p></div>}</div>)}{loading && <div className="max-w-[88%] rounded-3xl bg-brand/5 p-4 text-sm text-slate-500">Consultando dados autorizados...</div>}</div><form className="mt-5 flex gap-2 border-t border-stroke pt-4" onSubmit={submit}><input className="min-w-0 flex-1 rounded-xl border-stroke" value={question} onChange={event => setQuestion(event.target.value)} maxLength={500} placeholder="Ex.: Quanto vendi hoje?"/><Button disabled={loading || !question.trim()}><Send size={16} className="mr-2"/>Perguntar</Button></form></Card></div>
  </div>;
}
