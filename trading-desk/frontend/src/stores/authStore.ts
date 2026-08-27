import { create } from 'zustand';
import { api } from '@/api/client';

interface AuthState {
  token: string | null;
  username: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('access_token'),
  username: null,
  isAuthenticated: !!localStorage.getItem('access_token'),

  login: async (username, password) => {
    const res = await api.login(username, password);
    localStorage.setItem('access_token', res.access_token);
    set({ token: res.access_token, username, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('access_token');
    set({ token: null, username: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false, token: null, username: null });
      return;
    }
    try {
      const me = await api.me();
      set({ isAuthenticated: true, token, username: me.username });
    } catch {
      localStorage.removeItem('access_token');
      set({ isAuthenticated: false, token: null, username: null });
    }
  },
}));
