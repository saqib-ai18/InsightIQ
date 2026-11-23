import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark'

interface ThemeState {
  theme: Theme
  toggleTheme: () => void
  setTheme: (_theme: Theme) => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'dark',
      toggleTheme: () => set((_state) => ({ theme: _state.theme === 'dark' ? 'light' : 'dark' })),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'insightiq-theme',
      onRehydrateStorage: () => (state) => {
        if (state) {
          document.documentElement.classList.toggle('dark', state.theme === 'dark')
        }
      },
    }
  )
)

if (typeof window !== 'undefined') {
  useThemeStore.subscribe((state) => {
    document.documentElement.classList.toggle('dark', state.theme === 'dark')
  })
}