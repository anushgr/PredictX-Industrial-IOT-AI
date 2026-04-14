import { create } from "zustand";

interface DashboardState {
  isSidebarCollapsed: boolean;
  isMobileSidebarOpen: boolean;
  plant: string;
  toggleSidebar: () => void;
  setMobileSidebarOpen: (open: boolean) => void;
  setPlant: (plant: string) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  isSidebarCollapsed: false,
  isMobileSidebarOpen: false,
  plant: "Plant A",
  toggleSidebar: () =>
    set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
  setMobileSidebarOpen: (open) => set({ isMobileSidebarOpen: open }),
  setPlant: (plant) => set({ plant }),
}));
