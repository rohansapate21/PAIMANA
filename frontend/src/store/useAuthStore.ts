import { create } from 'zustand';
import { User, LoginRequest, login as apiLogin, logout as apiLogout } from '../api/client';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  initialize: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  initialize: () => {
    const token = localStorage.getItem('paimana_token');
    const userStr = localStorage.getItem('paimana_user');
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        set({ token, user, isAuthenticated: true });
      } catch {
        apiLogout();
        set({ token: null, user: null, isAuthenticated: false });
      }
    }
  },

  login: async (credentials) => {
    const res = await apiLogin(credentials);
    set({ token: res.access_token, user: res.user, isAuthenticated: true });
  },

  logout: () => {
    apiLogout();
    set({ token: null, user: null, isAuthenticated: false });
  },
}));

