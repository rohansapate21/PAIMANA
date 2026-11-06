import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { Navbar } from './components/Navbar';
import { Overview } from './pages/Overview';
import { ProjectsTable } from './pages/ProjectsTable';
import { ProjectDetail } from './pages/ProjectDetail';
import { AlertsFeed } from './pages/AlertsFeed';
import { AdminPanel } from './pages/AdminPanel';
import { Login } from './pages/Login';
import { useAuthStore } from './store/useAuthStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 60 * 1000, // 1 minute
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  const initializeAuth = useAuthStore((s) => s.initialize);

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col bg-slate-50">
          <Navbar />
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/projects" element={<ProjectsTable />} />
              <Route path="/projects/:uid" element={<ProjectDetail />} />
              <Route path="/alerts" element={<AlertsFeed />} />
              <Route path="/admin" element={<AdminPanel />} />
              <Route path="/login" element={<Login />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
            PAIMANA (Predictive Analytics & Infrastructure Monitoring) • SIH 2026 • Ministry of Statistics & Programme Implementation
          </footer>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;

