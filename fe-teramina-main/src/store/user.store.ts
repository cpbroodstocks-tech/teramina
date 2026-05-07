import { create } from "zustand";

interface UserData {
  name: string;
  email: string;
  phone: string;
  picture: string;
}

interface UserStoreState {
  user: UserData;
  setUser: (userData: UserData) => void;
}

export const useUserStore = create<UserStoreState>((set) => ({
  user: { name: "", email: "", phone: "", picture: "" },
  setUser: (userData) => set({ user: userData }),
}));
