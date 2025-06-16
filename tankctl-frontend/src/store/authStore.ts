// store/authStore.ts
import { create } from 'zustand';
import { devtools, persist, createJSONStorage } from 'zustand/middleware';
// import { encryptData, decryptData } from '@/lib/auth/tokenStorage'; // No longer directly used here

// Define the interface for the persisted state
interface PersistedAuthState {
  token: string | null;
  apiUrl: string | null;
}

// Define the interface for the auth state
interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  apiUrl: string | null;
  login: (token: string, apiUrl: string) => void;
  logout: () => void;
  setApiUrl: (url: string) => void;
}

// Custom storage (optional, but good for demonstration if you need custom logic)
// For simple localStorage, you can just use createJSONStorage(localStorage)
/*
const customStorage: StateStorage = {
  getItem: async (name: string): Promise<string | null> => {
    console.log(name, 'has been retrieved');
    return localStorage.getItem(name);
  },
  setItem: async (name: string, value: string): Promise<void> => {
    console.log(name, 'has been saved', value);
    localStorage.setItem(name, value);
  },
  removeItem: async (name: string): Promise<void> => {
    console.log(name, 'has been removed');
    localStorage.removeItem(name);
  },
};
*/

// Create the Zustand store with devtools and persist middleware
const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        isAuthenticated: false,
        token: null,
        apiUrl: null,
        login: (token, apiUrl) => set({ isAuthenticated: true, token, apiUrl }),
        logout: () => set({ isAuthenticated: false, token: null, apiUrl: null }),
        setApiUrl: (url) => set({ apiUrl: url }),
      }),
      {
        name: 'auth-storage',
        storage: createJSONStorage(() => localStorage),
        partialize: (state): PersistedAuthState => ({
          token: state.token,
          apiUrl: state.apiUrl,
        }),
        onRehydrateStorage: () => (state) => {
          // After rehydration, ensure isAuthenticated matches token presence
          if (state) {
            state.isAuthenticated = !!state.token;
          }
        },
        version: 1,
        migrate: (persistedState: any, version: number) => {
          // If we have old state, ensure it has the correct shape
          if (version === 0) {
            return {
              token: persistedState.token || null,
              apiUrl: persistedState.apiUrl || null,
            };
          }
          return persistedState;
        },
      }
    )
  )
);

export default useAuthStore;