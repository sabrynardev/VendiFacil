import { Component, type ErrorInfo, type PropsWithChildren } from "react";
import { Button } from "./Button";
import { Card } from "./Card";

export class ErrorBoundary extends Component<PropsWithChildren, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error("Unexpected screen error", { name: error.name, componentStack: info.componentStack }); }

  render() {
    if (this.state.failed) return <div className="flex min-h-[60vh] items-center justify-center p-4"><Card className="max-w-lg text-center"><h1 className="text-2xl font-semibold text-brandDeeper">Algo deu errado nesta tela.</h1><p className="mt-3 text-sm text-slate-600">Se houver vendas offline, elas continuam guardadas neste dispositivo.</p><Button className="mt-5" onClick={() => { this.setState({ failed: false }); window.location.reload(); }}>Tentar novamente</Button></Card></div>;
    return this.props.children;
  }
}
