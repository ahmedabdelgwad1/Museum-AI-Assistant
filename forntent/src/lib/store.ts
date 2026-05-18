import { create } from 'zustand'

interface MuseumStore {
  language: "en" | "ar"
  selectedSection: number | null
  setLanguage: (lang: "en" | "ar") => void
  setSelectedSection: (id: number) => void
}

export const useMuseumStore = create<MuseumStore>((set) => ({
  language: "en",
  selectedSection: null,
  setLanguage: (lang) => set({ language: lang }),
  setSelectedSection: (id) => set({ selectedSection: id }),
}))
