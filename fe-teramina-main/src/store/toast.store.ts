import { create } from "zustand";

interface ToastState {
  open: boolean;
  variant: "success" | "error" | "info";
  text: string;
}

interface ToastStoreState extends ToastState {
  setToast: (message: Partial<ToastState>) => void;
}

export const useToastStore = create<ToastStoreState>((set) => ({
  open: false,
  variant: "success",
  text: "",
  setToast: (message) => set((prev) => ({ ...prev, ...message })),
}));
