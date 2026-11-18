import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { FilterProvider } from './context/FilterContext';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { Shell } from './components/layout/Shell';

import { Landing } from './pages/Landing';
import { Login } from './pages/auth/Login';
import { Register } from './pages/auth/Register';
import { ForgotPassword } from './pages/auth/ForgotPassword';
import { Dashboard } from './pages/Dashboard';
import { EtaPredictor } from './pages/EtaPredictor';
import { Trends } from './pages/Trends';
import { DataEntry } from './pages/DataEntry';
import { Features } from './pages/Features';
import { Models } from './pages/Models';
import { Accuracy } from './pages/Accuracy';
import { Reports } from './pages/Reports';
import { Alerts } from './pages/Alerts';
import { Admin } from './pages/Admin';
import { Profile } from './pages/Profile';
import { About } from './pages/About';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 60000,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <FilterProvider>
          <BrowserRouter>
            <Routes>
              {/* Public Landing & Auth Routes */}
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />

              {/* Protected App Shell */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Shell />
                  </ProtectedRoute>
                }
              >
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="eta" element={<EtaPredictor />} />
                <Route path="trends" element={<Trends />} />

                {/* Analyst & Admin Routes */}
                <Route
                  path="data-entry"
                  element={
                    <ProtectedRoute allowedRoles={['analyst', 'admin']}>
                      <DataEntry />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="features"
                  element={
                    <ProtectedRoute allowedRoles={['analyst', 'admin']}>
                      <Features />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="models"
                  element={
                    <ProtectedRoute allowedRoles={['analyst', 'admin']}>
                      <Models />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="accuracy"
                  element={
                    <ProtectedRoute allowedRoles={['analyst', 'admin']}>
                      <Accuracy />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="reports"
                  element={
                    <ProtectedRoute allowedRoles={['analyst', 'admin']}>
                      <Reports />
                    </ProtectedRoute>
                  }
                />

                {/* System Alerts */}
                <Route path="alerts" element={<Alerts />} />

                {/* Admin Management */}
                <Route
                  path="admin"
                  element={
                    <ProtectedRoute allowedRoles={['admin']}>
                      <Admin />
                    </ProtectedRoute>
                  }
                />

                {/* User Profile & Methodology */}
                <Route path="profile" element={<Profile />} />
                <Route path="about" element={<About />} />
              </Route>

              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </BrowserRouter>
        </FilterProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
