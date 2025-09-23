'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type SettingsState = {
  topK: number
  setTopK: (n: number) => void
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    set => ({
      topK: 2,
      setTopK: n => set({ topK: Math.max(1, n) }),
    }),
    { name: 'settings' }
  )
)
