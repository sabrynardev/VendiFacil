import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { ToastProvider } from "./components/ToastProvider";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ConnectivityProvider } from "./contexts/ConnectivityContext";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { AppLayout } from "./layouts/AppLayout";
import { brand } from "./config/brand";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";

const CashierPage = lazy(() => import("./pages/CashierPage").then((module) => ({ default: module.CashierPage })));
const CashRegistersPage = lazy(() => import("./pages/CashRegistersPage").then((module) => ({ default: module.CashRegistersPage })));
const CategoriesPage = lazy(() => import("./pages/CategoriesPage").then((module) => ({ default: module.CategoriesPage })));
const AuditPage = lazy(() => import("./pages/AuditPage").then((module) => ({ default: module.AuditPage })));
const DashboardPage = lazy(() => import("./pages/DashboardPage").then((module) => ({ default: module.DashboardPage })));
const InventoryPage = lazy(() => import("./pages/InventoryPage").then((module) => ({ default: module.InventoryPage })));
const IntelligencePage = lazy(() => import("./pages/IntelligencePage").then((module) => ({ default: module.IntelligencePage })));
const AskVendiPage = lazy(() => import("./pages/AskVendiPage").then((module) => ({ default: module.AskVendiPage })));
const InventoryCountsPage = lazy(() => import("./pages/InventoryCountsPage").then((module) => ({ default: module.InventoryCountsPage })));
const LotsPage = lazy(() => import("./pages/LotsPage").then((module) => ({ default: module.LotsPage })));
const PurchasesPage = lazy(() => import("./pages/PurchasesPage").then((module) => ({ default: module.PurchasesPage })));
const CustomersPage = lazy(() => import("./pages/CustomersPage").then((module) => ({ default: module.CustomersPage })));
const FinancialPage = lazy(() => import("./pages/FinancialPage").then((module) => ({ default: module.FinancialPage })));
const MarketingPage = lazy(() => import("./pages/MarketingPage").then((module) => ({ default: module.MarketingPage })));
const ProductsPage = lazy(() => import("./pages/ProductsPage").then((module) => ({ default: module.ProductsPage })));
const ReportsPage = lazy(() => import("./pages/ReportsPage").then((module) => ({ default: module.ReportsPage })));
const SalesPage = lazy(() => import("./pages/SalesPage").then((module) => ({ default: module.SalesPage })));
const SettingsPage = lazy(() => import("./pages/SettingsPage").then((module) => ({ default: module.SettingsPage })));
const SuppliersPage = lazy(() => import("./pages/SuppliersPage").then((module) => ({ default: module.SuppliersPage })));
const UsersPage = lazy(() => import("./pages/UsersPage").then((module) => ({ default: module.UsersPage })));
const SynchronizationPage = lazy(() => import("./pages/SynchronizationPage").then((module) => ({ default: module.SynchronizationPage })));

function ScreenLoader() {
  return <div className="flex min-h-screen items-center justify-center text-slate-500">Carregando {brand.shortName}...</div>;
}

function PrivateRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return <ScreenLoader />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <AppLayout />;
}

function PublicRoutes() {
  const { user } = useAuth();

  if (user) {
    return <Navigate to="/" replace />;
  }

  return <LoginPage />;
}

function HomeRoute() {
  const { user } = useAuth();
  if (user?.permissions.includes("dashboard.view")) return <DashboardPage />;
  return <Navigate to="/cashier" replace />;
}

function PermissionRoute({ permission, children }: { permission: string; children: React.ReactNode }) {
  const { user } = useAuth();
  return user?.permissions.includes(permission) ? children : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <ConnectivityProvider>
        <ToastProvider>
          <ErrorBoundary>
            <Suspense fallback={<ScreenLoader />}>
          <Routes>
            <Route path="/apresentacao" element={<MarketingPage />} />
            <Route path="/login" element={<PublicRoutes />} />
            <Route path="/registro" element={<RegisterPage />} />
            <Route path="/" element={<PrivateRoutes />}>
              <Route index element={<HomeRoute />} />
              <Route path="cashier" element={<PermissionRoute permission="cashier.operate"><CashierPage /></PermissionRoute>} />
              <Route path="cash-registers" element={<PermissionRoute permission="cash_register.view"><CashRegistersPage /></PermissionRoute>} />
              <Route path="products" element={<PermissionRoute permission="products.view"><ProductsPage /></PermissionRoute>} />
              <Route path="categories" element={<PermissionRoute permission="products.manage"><CategoriesPage /></PermissionRoute>} />
              <Route path="inventory" element={<PermissionRoute permission="inventory.view"><InventoryPage /></PermissionRoute>} />
              <Route path="lots" element={<PermissionRoute permission="lots.view"><LotsPage /></PermissionRoute>} />
              <Route path="inventory-counts" element={<PermissionRoute permission="inventory.count"><InventoryCountsPage /></PermissionRoute>} />
              <Route path="sales" element={<PermissionRoute permission="sales.view"><SalesPage /></PermissionRoute>} />
              <Route path="suppliers" element={<PermissionRoute permission="suppliers.view"><SuppliersPage /></PermissionRoute>} />
              <Route path="purchases" element={<PermissionRoute permission="purchases.view"><PurchasesPage /></PermissionRoute>} />
              <Route path="customers" element={<PermissionRoute permission="customers.view"><CustomersPage /></PermissionRoute>} />
              <Route path="financial" element={<PermissionRoute permission="financial.view"><FinancialPage /></PermissionRoute>} />
              <Route path="reports" element={<PermissionRoute permission="reports.view"><ReportsPage /></PermissionRoute>} />
              <Route path="intelligence" element={<PermissionRoute permission="intelligence.view"><IntelligencePage /></PermissionRoute>} />
              <Route path="ask-vendi" element={<PermissionRoute permission="assistant.ask"><AskVendiPage /></PermissionRoute>} />
              <Route path="users" element={<PermissionRoute permission="users.manage"><UsersPage /></PermissionRoute>} />
              <Route path="audit" element={<PermissionRoute permission="audit.view"><AuditPage /></PermissionRoute>} />
              <Route path="settings" element={<PermissionRoute permission="settings.view"><SettingsPage /></PermissionRoute>} />
              <Route path="synchronization" element={<PermissionRoute permission="cashier.operate"><SynchronizationPage /></PermissionRoute>} />
            </Route>
          </Routes>
            </Suspense>
          </ErrorBoundary>
        </ToastProvider>
      </ConnectivityProvider>
    </AuthProvider>
  );
}
