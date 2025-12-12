import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { StrategyProvider } from './context/StrategyContext';
import ErrorBoundary from './components/ErrorBoundary';
import ConnectionStatus from './components/ConnectionStatus';
import TradingNotification from './components/TradingNotification';
import MainLayout from './components/layout/MainLayout';

// Lazy load pages for better initial load performance
const Login = lazy(() => import('./pages/Login'));
const OAuthCallback = lazy(() => import('./pages/OAuthCallback'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Strategy = lazy(() => import('./pages/Strategy'));
const Trading = lazy(() => import('./pages/Trading'));
const TradingHistory = lazy(() => import('./pages/TradingHistory'));
const Settings = lazy(() => import('./pages/Settings'));
const Alerts = lazy(() => import('./pages/Alerts'));
const Notifications = lazy(() => import('./pages/Notifications'));
const BacktestingPage = lazy(() => import('./pages/BacktestingPage'));
const BotManagement = lazy(() => import('./pages/BotManagement'));

// Admin pages
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'));
const GridTemplateManager = lazy(() => import('./pages/admin/GridTemplateManager'));

// Loading spinner component - Clean & Minimal
const PageLoader = () => (
  <div
    style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: '#fafafa',
      gap: '24px',
    }}
  >
    <div
      style={{
        width: '48px',
        height: '48px',
        border: '3px solid #e8e8ed',
        borderTopColor: '#0071e3',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }}
    />
    <style>
      {`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}
    </style>
    <p
      style={{
        fontSize: '15px',
        color: '#86868b',
        fontWeight: 500,
        margin: 0,
      }}
    >
      로딩 중...
    </p>
  </div>
);

// Protected Route Component (for regular users)
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          background: '#fafafa',
          gap: '24px',
        }}
      >
        <div
          style={{
            width: '48px',
            height: '48px',
            border: '3px solid #e8e8ed',
            borderTopColor: '#0071e3',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <p
          style={{
            fontSize: '15px',
            color: '#86868b',
            fontWeight: 500,
            margin: 0,
          }}
        >
          인증 확인 중...
        </p>
      </div>
    );
  }

  return isAuthenticated ? <MainLayout>{children}</MainLayout> : <Navigate to="/login" />;
}


function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <WebSocketProvider>
            <StrategyProvider>
              <Router>
                <Suspense fallback={<PageLoader />}>
                  <Routes>
                    <Route path="/" element={<Login />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/oauth/callback" element={<OAuthCallback />} />
                    <Route
                      path="/dashboard"
                      element={
                        <ProtectedRoute>
                          <Dashboard />
                        </ProtectedRoute>
                      }
                    />

                    <Route
                      path="/strategy"
                      element={
                        <ProtectedRoute>
                          <Strategy />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/trading"
                      element={
                        <ProtectedRoute>
                          <Trading />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/history"
                      element={
                        <ProtectedRoute>
                          <TradingHistory />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/alerts"
                      element={
                        <ProtectedRoute>
                          <Alerts />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/notifications"
                      element={
                        <ProtectedRoute>
                          <Notifications />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/backtesting"
                      element={
                        <ProtectedRoute>
                          <BacktestingPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/settings"
                      element={
                        <ProtectedRoute>
                          <Settings />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/bots"
                      element={
                        <ProtectedRoute>
                          <BotManagement />
                        </ProtectedRoute>
                      }
                    />

                    {/* Admin Routes */}
                    <Route
                      path="/admin"
                      element={
                        <ProtectedRoute>
                          <AdminDashboard />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/admin/grid-templates"
                      element={
                        <ProtectedRoute>
                          <GridTemplateManager />
                        </ProtectedRoute>
                      }
                    />
                  </Routes>
                </Suspense>
              </Router>
              <ConnectionStatus />
              <TradingNotification />
            </StrategyProvider>
          </WebSocketProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
