// store/authStore.ts
import { create } from 'zustand';
import { devtools, persist, createJSONStorage, StateStorage } from 'zustand/middleware';
// import { encryptData, decryptData } from '@/lib/auth/tokenStorage'; // No longer directly used here

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  apiUrl: string | null;
  login: (token: string, apiUrl: string) => void;
  logout: () => void;
  setApiUrl: (url: string) => void;
  // Add other state properties and actions as needed
}

// Define the interface for the persisted state
interface PersistedAuthState {
  token: string | null;
  apiUrl: string | null;
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
        name: 'auth-storage', // unique name for localStorage key
        storage: createJSONStorage(() => localStorage), // or customStorage
        // Explicitly type the partialize function to return PersistedAuthState
        partialize: (state): PersistedAuthState => ({
          token: state.token,
          apiUrl: state.apiUrl,
        }),
        // Optional: onRehydrateStorage for custom rehydration logic
        onRehydrateStorage: (state) => {
          console.log('hydration starts');
          if (state) {
            (state as AuthState).isAuthenticated = !!state.token; 
          }
          return (persistedState, currentState) => {
            console.log('hydration finished', persistedState, currentState);
          };
        },
        // Optional: versioning for migrations
        version: 1,
        migrate: (persistedState: any, version: number) => {
          if (version === 0) {
            // if the storage is from version 0, we should migrate it to version 1
            // For example, if 'token' was previously 'jwtToken'
            // const state = persistedState as AuthStateV0;
            // return { token: state.jwtToken, apiUrl: state.apiUrl };
          }
          return persistedState as AuthState;
        },
      }
    )
  )
);

export default useAuthStore;