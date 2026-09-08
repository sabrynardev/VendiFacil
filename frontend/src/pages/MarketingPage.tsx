import { ArrowRight, BarChart3, Boxes, CheckCircle2, CreditCard, ShieldCheck, ShoppingCart, Store, TimerReset } from "lucide-react";
import { Link } from "react-router-dom";
import { brand } from "../config/brand";
import { Button } from "../components/Button";
import { Card } from "../components/Card";

const highlights = [
  {
    icon: ShoppingCart,
    title: "Venda rápida no caixa",
    description: "Busca por nome, SKU ou código de barras com fluxo otimizado para operação diária.",
  },
  {
    icon: Boxes,
    title: "Estoque com previsão",
    description: "Baixa automática, alertas de ruptura e recomendação de reposição baseada em giro.",
  },
  {
    icon: BarChart3,
    title: "Gestão em tempo real",
    description: "Dashboard, histórico de vendas e relatórios para acompanhar a saúde do negócio.",
  },
];

const objections = [
  "Instalação assistida e treinamento inicial",
  "Funciona bem para mercadinho, conveniência, adega e mini mercado",
  "Fluxo visual pronto para demonstração e para uso local",
  "Base preparada para evoluir com PostgreSQL e suporte contínuo",
];

export function MarketingPage() {
  return (
    <div className="min-h-screen bg-background text-brandDeeper">
      <section className="relative overflow-hidden border-b border-stroke/70">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(2,59,230,0.12),_transparent_25%),radial-gradient(circle_at_bottom_right,_rgba(1,28,107,0.1),_transparent_26%),linear-gradient(180deg,#f8fbff_0%,#edf4ff_100%)]" />
        <div className="relative mx-auto max-w-7xl px-5 py-8 md:px-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-brand">{brand.companyName}</p>
              <h1 className="mt-3 max-w-4xl text-3xl font-semibold tracking-tight md:text-5xl">{brand.productName}</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 md:text-lg">{brand.sellerPitch}</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <a href={brand.supportWhatsAppUrl} target="_blank" rel="noreferrer">
                <Button className="px-5 py-3">Quero uma demonstração</Button>
              </a>
              <Link to="/login">
                <Button variant="secondary" className="px-5 py-3">
                  Entrar no sistema
                </Button>
              </Link>
            </div>
          </div>

          <div className="mt-10 grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
            <Card className="overflow-hidden p-0 border-brand/10">
              <div className="grid gap-6 bg-[radial-gradient(circle_at_top_left,_rgba(2,59,230,0.10),_transparent_30%),linear-gradient(180deg,#ffffff_0%,#edf4ff_100%)] px-6 py-7 md:px-8">
                <div className="flex flex-wrap gap-3 text-xs uppercase tracking-[0.22em] text-slate-600">
                  <span className="rounded-full border border-stroke bg-brand/5 px-3 py-1.5">PDV</span>
                  <span className="rounded-full border border-stroke bg-brand/5 px-3 py-1.5">Estoque</span>
                  <span className="rounded-full border border-stroke bg-brand/5 px-3 py-1.5">Dashboard</span>
                  <span className="rounded-full border border-stroke bg-brand/5 px-3 py-1.5">Relatórios</span>
                </div>
                <h2 className="max-w-3xl text-3xl font-semibold leading-tight md:text-4xl">
                  Venda mais rápido, reduza erros no caixa e acompanhe o estoque sem planilhas soltas.
                </h2>
                <p className="max-w-2xl text-sm leading-6 text-slate-600 md:text-base">
                  Solução pensada para comerciantes que precisam de um sistema claro, bonito e prático para o dia a dia. Ideal para quem quer sair da improvisação sem cair em software pesado demais.
                </p>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded-2xl border border-stroke bg-white/85 p-4">
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Fluxo principal</p>
                    <p className="mt-2 text-xl font-semibold">Venda + estoque + histórico</p>
                  </div>
                  <div className="rounded-2xl border border-stroke bg-white/85 p-4">
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Perfil ideal</p>
                    <p className="mt-2 text-xl font-semibold">Mercadinho e conveniência</p>
                  </div>
                  <div className="rounded-2xl border border-stroke bg-white/85 p-4">
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Modelo comercial</p>
                    <p className="mt-2 text-xl font-semibold">Implantação + suporte</p>
                  </div>
                </div>
              </div>
            </Card>

            <Card className="flex flex-col justify-between border-brand/10">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-brandStrong">Oferta local</p>
                <h3 className="mt-3 text-2xl font-semibold">Ideal para vender regionalmente com atendimento próximo.</h3>
                <div className="mt-6 space-y-4">
                  {objections.map((item) => (
                    <div key={item} className="flex items-start gap-3 rounded-2xl border border-stroke/70 bg-brand/4 px-4 py-3">
                      <CheckCircle2 className="mt-0.5 text-brand" size={18} />
                      <p className="text-sm leading-6 text-slate-600">{item}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-8 rounded-2xl border border-stroke bg-brand/4 p-4 text-sm text-slate-600">
                <p className="font-medium text-brandDeeper">{brand.companyName}</p>
                <p className="mt-1">{brand.companyTagline}</p>
                <p className="mt-3">{brand.supportEmail}</p>
                <p>{brand.supportPhone}</p>
              </div>
            </Card>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-14 md:px-8">
        <div className="mb-8">
          <p className="text-xs uppercase tracking-[0.35em] text-brand">Recursos</p>
          <h2 className="mt-3 text-3xl font-semibold">O que você entrega para o cliente local</h2>
        </div>
        <div className="grid gap-5 lg:grid-cols-3">
          {highlights.map((item) => {
            const Icon = item.icon;
            return (
              <Card key={item.title} className="h-full">
                <div className="inline-flex rounded-2xl bg-brand/15 p-3 text-brand">
                  <Icon size={22} />
                </div>
                <h3 className="mt-5 text-xl font-semibold">{item.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-600">{item.description}</p>
              </Card>
            );
          })}
        </div>
      </section>

      <section className="border-y border-stroke/70 bg-[linear-gradient(180deg,rgba(2,59,230,0.02),rgba(1,17,66,0.03))]">
        <div className="mx-auto max-w-7xl px-5 py-14 md:px-8">
          <div className="mb-8">
            <p className="text-xs uppercase tracking-[0.35em] text-brand">Planos sugeridos</p>
            <h2 className="mt-3 text-3xl font-semibold">Estrutura simples para vender logo no primeiro cliente</h2>
          </div>
          <div className="grid gap-5 lg:grid-cols-3">
            {brand.implementationPlans.map((plan, index) => (
              <Card key={plan.name} className={index === 1 ? "border-brand/30 bg-brand/5" : ""}>
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-semibold">{plan.name}</h3>
                  {index === 1 && <span className="rounded-full bg-brand/15 px-3 py-1 text-xs font-semibold text-brand">Mais equilibrado</span>}
                </div>
                <p className="mt-4 text-4xl font-semibold">{plan.price}</p>
                <p className="mt-4 text-sm leading-6 text-slate-600">{plan.description}</p>
                <a href={brand.supportWhatsAppUrl} target="_blank" rel="noreferrer">
                  <Button className="mt-6 w-full">
                    Solicitar proposta
                    <ArrowRight size={16} className="ml-2" />
                  </Button>
                </a>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-14 md:px-8">
        <div className="mb-8">
          <p className="text-xs uppercase tracking-[0.35em] text-brand">Como vender</p>
          <h2 className="mt-3 text-3xl font-semibold">Narrativa comercial pronta para abordagem local</h2>
        </div>
        <div className="grid gap-5 lg:grid-cols-4">
          {[
            {
              icon: Store,
              title: "Escolha o nicho",
              description: "Mercadinho, conveniência, adega ou mini mercado com operação simples e dono acessível.",
            },
            {
              icon: TimerReset,
              title: "Mostre o antes/depois",
              description: "Troque a conversa técnica por ganho prático: menos bagunça, mais controle e venda rápida.",
            },
            {
              icon: CreditCard,
              title: "Venda implantação",
              description: "No começo, a receita vem mais fácil com setup, treinamento e suporte local.",
            },
            {
              icon: ShieldCheck,
              title: "Feche com confiança",
              description: "Use o dashboard, o histórico e a baixa de estoque como prova de que o sistema resolve algo real.",
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <Card key={item.title}>
                <div className="inline-flex rounded-2xl bg-brand/10 p-3 text-brand">
                  <Icon size={22} />
                </div>
                <h3 className="mt-4 text-lg font-semibold">{item.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-600">{item.description}</p>
              </Card>
            );
          })}
        </div>
      </section>

      <section className="px-5 pb-16 md:px-8">
        <div className="mx-auto max-w-7xl overflow-hidden rounded-[2rem] border border-stroke bg-[radial-gradient(circle_at_top_left,_rgba(2,59,230,0.10),_transparent_24%),linear-gradient(180deg,#ffffff_0%,#edf4ff_100%)] px-6 py-8 md:px-10 md:py-10">
          <div className="grid gap-6 md:grid-cols-[1.2fr_0.8fr] md:items-center">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-brand">Pronto para apresentar</p>
              <h2 className="mt-3 text-3xl font-semibold md:text-4xl">Use esta página como vitrine comercial, roteiro de demo e ponto de captação.</h2>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 md:text-base">
                Se quiser transformar isso em uma operação de vendas local, o próximo passo é trocar os contatos pelos seus dados reais e começar a agendar demonstrações.
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <a href={brand.supportWhatsAppUrl} target="_blank" rel="noreferrer">
                <Button className="w-full py-3 text-base">Falar no WhatsApp</Button>
              </a>
              <Link to="/login">
                <Button variant="secondary" className="w-full py-3 text-base">
                  Acessar demo do sistema
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
