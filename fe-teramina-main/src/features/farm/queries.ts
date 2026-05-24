import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import browserAxios from "axios";
import { axios } from "helper/axios";

export const farmKeys = {
  list: ["farms"] as const,
};

export const useFarmList = () =>
  useQuery({
    queryKey: farmKeys.list,
    queryFn: () => axios.get("/farm/list-farm").then((r: any) => r.payload),
  });

export const useInvalidateFarmList = () => {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: farmKeys.list });
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
