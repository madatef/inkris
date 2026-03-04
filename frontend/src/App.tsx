import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import AppLayout from '@/components/layout/AppLayout'
import { Toaster } from 'sonner'
import { useAuthStore } from './stores/auth-store'
import { useSSE } from './hooks/use-sse'

import LandingPage from '@/pages/LandingPage'
import LoginPage from '@/pages/LoginPage'
import SignupPage from '@/pages/SignupPage'
import DashboardPage from '@/pages/DashboardPage'
import FilesPage from '@/pages/FilesPage'
import ChatPage from '@/pages/ChatPage'
import ProfilePage from '@/pages/ProfilePage'


function App() {
  const { checkAuth, isAuthenticated } = useAuthStore();
  useSSE();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <LoginPage />} />
        <Route path="/signup" element={isAuthenticated ? <Navigate to="/dashboard" /> : <SignupPage />} />
        
        <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/chat/:id?" element={<ChatPage />} />
          <Route path="/files" element={<FilesPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>
      </Routes>
      <Toaster richColors position="top-center" />
    </>
  );
}

export default App;