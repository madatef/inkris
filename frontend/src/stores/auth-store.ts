import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import apiClient from '@/lib/api-client';
import type { UserResponse, UserCreate, UserLogin } from '@/types/api';

interface AuthState {
  user: UserResponse | null;
  isAuthenticated: boolean;
  hasCheckedAuth: boolean;
  isLoading: boolean;
  error: string | null;

  login: (credentials: UserLogin) => Promise<void>;
  signup: (data: UserCreate) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  clearError: () => void;
  setUser: (user: UserResponse | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      hasCheckedAuth: false,
      isLoading: false,
      error: null,

      login: async (credentials) => {
        set({ isLoading: true, error: null });
        try {
          const user = await apiClient.post<UserResponse>(
            '/auth/login',
            credentials
          );
          set({ user, isAuthenticated: true });
        } catch (error: any) {
          set({
            user: null,
            isAuthenticated: false,
            error: error.message || 'Failed to login',
          });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      signup: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const user = await apiClient.post<UserResponse>(
            '/auth/signup',
            data
          );
          set({ user, isAuthenticated: true });
        } catch (error: any) {
          set({
            user: null,
            isAuthenticated: false,
            error: error.message || 'Failed to create account',
          });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      logout: async () => {
        set({ isLoading: true, error: null });
        try {
          await apiClient.post('/auth/logout');
          set({ user: null, isAuthenticated: false });
        } finally {
          set({ isLoading: false });
        }
      },

      checkAuth: async () => {
        set({ isLoading: true });
        try {
          const user = await apiClient.get<UserResponse>('/auth/me');
          set({ user, isAuthenticated: true });
        } catch {
          set({ user: null, isAuthenticated: false });
        } finally {
          set({ isLoading: false, hasCheckedAuth: true });
        }
      },

      refreshToken: async () => {
        try {
          await apiClient.post('/auth/refresh');
          return true;
        } catch {
          set({ user: null, isAuthenticated: false });
          return false;
        }
      },

      clearError: () => set({ error: null }),

      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
        }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);