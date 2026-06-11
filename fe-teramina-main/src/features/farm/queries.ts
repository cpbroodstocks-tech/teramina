import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import browserAxios from "axios";
import { axios } from "helper/axios";

export const farmKeys = {
  list: ["farms"] as const,
  hierarchy: (includeArchived: boolean) => ["farm-hierarchy", includeArchived] as const,
};

export interface CycleHierarchyItem {
  id: string;
  name: string;
  pond_id: string;
  start_date: string;
  is_active: boolean;
  is_archived: boolean;
  dashboard_ready: boolean;
}

export interface PondHierarchyItem {
  id: string;
  name: string;
  farm_id: string;
  size: number;
  pond_construction: string;
  pond_shape: string;
  is_active: boolean;
  is_archived: boolean;
  active_cycle_id: string;
  cycles: CycleHierarchyItem[];
}

export interface FarmHierarchyItem {
  id: string;
  name: string;
  location: string;
  is_archived: boolean;
  ponds: PondHierarchyItem[];
}

export const useFarmHierarchy = (includeArchived = false) =>
  useQuery({
    queryKey: farmKeys.hierarchy(includeArchived),
    queryFn: () =>
      axios.get(`/farm/hierarchy?include_archived=${includeArchived}`).then((r: any) => r.payload?.farms ?? []) as Promise<FarmHierarchyItem[]>,
  });

const useHierarchyMutation = (endpoint: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => axios.post(`${endpoint}${id}`).then((r: any) => r.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["farm-hierarchy"] }),
  });
};

export const useArchiveFarm = () => useHierarchyMutation("/farm/archive-farm?farm_id=");
export const useRestoreFarm = () => useHierarchyMutation("/farm/restore-farm?farm_id=");
export const useArchivePond = () => useHierarchyMutation("/pond/archive-pond?pond_id=");
export const useRestorePond = () => useHierarchyMutation("/pond/restore-pond?pond_id=");
export const useArchiveCycle = () => useHierarchyMutation("/cycle/archive-cycle?cycle_id=");
export const useRestoreCycle = () => useHierarchyMutation("/cycle/restore-cycle?cycle_id=");

export const useSetActiveCycle = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ pondId, cycleId }: { pondId: string; cycleId: string }) =>
      axios.post(`/pond/set-active-cycle?pond_id=${pondId}&cycle_id=${cycleId}`).then((r: any) => r.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["farm-hierarchy"] }),
  });
};

export const useFarmList = () =>
  useQuery({
    queryKey: farmKeys.list,
    queryFn: () => axios.get("/farm/list-farm").then((r: any) => r.payload),
  });

export const useInvalidateFarmList = () => {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: farmKeys.list });
    queryClient.invalidateQueries({ queryKey: ["farm-hierarchy"] });
  };
};

export const useAddFarm = () => {
  const invalidate = useInvalidateFarmList();
  return useMutation({
    mutationFn: (data: { name: string; location: string }) =>
      axios.post("/farm/add-farm", data).then((r: any) => r.payload),
    onSuccess: () => invalidate(),
  });
};

export const useEditFarm = () => {
  const invalidate = useInvalidateFarmList();
  return useMutation({
    mutationFn: ({ farm_id, ...data }: { farm_id: string; name: string; location: string }) =>
      axios.put(`/farm/update-farm?farm_id=${farm_id}`, data).then((r: any) => r.payload),
    onSuccess: () => invalidate(),
  });
};

export const useDeleteFarm = () => {
  const invalidate = useInvalidateFarmList();
  return useMutation({
    mutationFn: (farm_id: string) =>
      axios.delete(`/farm/delete-farm?farm_id=${farm_id}`).then((r: any) => r.payload),
    onSuccess: () => invalidate(),
  });
};

export const fetchCityRegion = async (url: string) => {
  const response = await browserAxios.get(url);
  if (!response) throw new Error("Failed to fetch city region");
  return response.data;
};
