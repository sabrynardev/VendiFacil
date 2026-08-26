import { BarChart3, Boxes, Cog, LayoutDashboard, LogOut, Menu, PackageSearch, ReceiptText, ShoppingCart, Truck } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/cashier", label: "Caixa", icon: ShoppingCart },
  { to: "/products", label: "Produtos", icon: PackageSearch },
  { to: "/inventory", label: "Estoque", icon: Boxes },
  { to: "/sales", label: "Vendas", icon: ReceiptText },
  { to: "/suppliers", label: "Fornecedores", icon: Truck },
  { to: "/reports", label: "Relatórios", icon: BarChart3 },
  { to: "/settings", label: "Configurações", icon: Cog },
];

export function AppLayout() {
  const { user, signOut } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const roleLabel =
    user?.role === "ADMIN" ? "Administrador" : user?.role === "CAIXA" ? "Operação de caixa" : "Gestão de estoque";

  const navigation = (
    <nav className="mt-8 space-y-2">
      {links.map((link) => {
        const Icon = link.icon;
        return (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === "/"}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition ${
                isActive ? "bg-brand text-white shadow-soft" : "text-slate-300 hover:bg-slate-900/80"
              }`
            }
          >
            <Icon size={18} />
            {link.label}
          </NavLink>
        );
      })}
    </nav>
  );

  return (
    <div className="flex min-h-screen bg-transparent">
      <aside className="hidden w-72 flex-col border-r border-stroke bg-slate-950/60 p-6 lg:flex">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-brand">VendiFácil</p>
          <h1 className="mt-3 text-2xl font-semibold">Smart Point of Sale</h1>
          <p className="mt-2 text-sm text-slate-400">PDV moderno para mercadinhos, conveniência e operação diária.</p>
        </div>
        {navigation}
        <div className="mt-auto rounded-2xl border border-stroke bg-surface/90 p-4">
          <p className="text-sm font-medium text-slate-100">{user?.name}</p>
          <p className="mt-1 text-xs text-slate-400">{roleLabel}</p>
          <button className="mt-4 flex items-center gap-2 text-sm text-slate-300" onClick={signOut}>
            <LogOut size={16} />
            Sair
          </button>
        </div>
      </aside>
      <main className="flex-1 p-4 md:p-6 lg:p-8">
        <div className="mb-6 flex items-center justify-between rounded-2xl border border-stroke bg-slate-950/50 px-4 py-3 shadow-soft lg:hidden">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-brand">VendiFácil</p>
            <p className="mt-1 text-sm text-slate-400">{roleLabel}</p>
          </div>
          <button
            className="rounded-2xl border border-stroke bg-surface p-3 text-slate-200"
            onClick={() => setMobileOpen((current) => !current)}
          >
            <Menu size={18} />
          </button>
        </div>
        {mobileOpen && (
          <div className="mb-6 rounded-3xl border border-stroke bg-slate-950/85 p-4 shadow-soft lg:hidden">
            {navigation}
            <div className="mt-6 rounded-2xl border border-stroke bg-surface/90 p-4">
              <p className="text-sm font-medium text-slate-100">{user?.name}</p>
              <p className="mt-1 text-xs text-slate-400">{roleLabel}</p>
              <button className="mt-4 flex items-center gap-2 text-sm text-slate-300" onClick={signOut}>
                <LogOut size={16} />
                Sair
              </button>
            </div>
          </div>
        )}
        <Outlet />
      </main>
    </div>
  );
}
