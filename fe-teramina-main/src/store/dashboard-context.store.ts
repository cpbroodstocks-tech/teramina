import { create } from "zustand";

export interface DashboardContext {
  farm_id: string;
  farm_name: string;
  pond_id: string;
  pond_name: string;
  cycle_id: string;
  cycle_name: string;
}

const EMPTY_CONTEXT: DashboardContext = {
  farm_id: "",
  farm_name: "",
  pond_id: "",
  pond_name: "",
  cycle_id: "",
  cycle_name: "",
};

const readContext = (): DashboardContext => {
  if (typeof window === "undefined") return EMPTY_CONTEXT;
  return Object.fromEntries(
    Object.keys(EMPTY_CONTEXT).map((key) => [key, localStorage.getItem(key) || ""])
  ) as unknown as DashboardContext;
};

const writeContext = (context: DashboardContext) => {
  if (typeof window === "undefined") return;
  Object.entries(context).forEach(([key, value]) => {
    if (value) localStorage.setItem(key, value);
    else localStorage.removeItem(key);
  });
};

interface DashboardContextStore extends DashboardContext {
  setContext: (context: Partial<DashboardContext>) => void;
  clearContext: () => void;
}

export const useDashboardContextStore = create<DashboardContextStore>((set) => ({
  ...readContext(),
  setContext: (context) =>
    set((previous) => {
      const next = {
        farm_id: context.farm_id ?? previous.farm_id,
        farm_name: context.farm_name ?? previous.farm_name,
        pond_id: context.pond_id ?? previous.pond_id,
        pond_name: context.pond_name ?? previous.pond_name,
        cycle_id: context.cycle_id ?? previous.cycle_id,
        cycle_name: context.cycle_name ?? previous.cycle_name,
      };
      writeContext(next);
      return next;
    }),
  clearContext: () =>
    set(() => {
      writeContext(EMPTY_CONTEXT);
      return EMPTY_CONTEXT;
    }),
}));

export const getDashboardContext = () => readContext();
