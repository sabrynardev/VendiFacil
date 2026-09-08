import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { ToastProvider } from "./components/ToastProvider";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { AppLayout } from "./layouts/AppLayout";
import { brand } from "./config/brand";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";

const CashierPage = lazy(() => import("./pages/CashierPage").then((module) => ({ default: module.CashierPage })));
const DashboardPage = lazy(() => import("./pages/DashboardPage").then((module) => ({ default: module.DashboardPage })));
const InventoryPage = lazy(() => import("./pages/InventoryPage").then((module) => ({ default: module.InventoryPage })));
const MarketingPage = lazy(() => import("./pages/MarketingPage").then((module) => ({ default: module.MarketingPage })));
const ProductsPage = lazy(() => import("./pages/ProductsPage").then((module) => ({ default: module.ProductsPage })));
const ReportsPage = lazy(() => import("./pages/ReportsPage").then((module) => ({ default: module.ReportsPage })));
const SalesPage = lazy(() => import("./pages/SalesPage").then((module) => ({ default: module.SalesPage })));
const SettingsPage = lazy(() => import("./pages/SettingsPage").then((module) => ({ default: module.SettingsPage })));
const SuppliersPage = lazy(() => import("./pages/SuppliersPage").then((module) => ({ default: module.SuppliersPage })));

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

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Suspense fallback={<ScreenLoader />}>
          <Routes>
            <Route path="/apresentacao" element={<MarketingPage />} />
            <Route path="/login" element={<PublicRoutes />} />
            <Route path="/registro" element={<RegisterPage />} />
            <Route path="/" element={<PrivateRoutes />}>
              <Route index element={<DashboardPage />} />
              <Route path="cashier" element={<CashierPage />} />
              <Route path="products" element={<ProductsPage />} />
              <Route path="inventory" element={<InventoryPage />} />
              <Route path="sales" element={<SalesPage />} />
              <Route path="suppliers" element={<SuppliersPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </Suspense>
      </ToastProvider>
    </AuthProvider>
  );
}
