import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { axios } from "helper/axios";

export const cycleKeys = {
  list: (params: Record<string, string>) => ["cycles", params] as const,
};

export const useInvalidateCycleList = () => {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["cycles"] });
    queryClient.invalidateQueries({ queryKey: ["farm-hierarchy"] });
  };
};

export const useCycleList = () => {
  const params = useParams() as Record<string, string>;
  const queryString = new URLSearchParams(params).toString();
  return useQuery({
    queryKey: cycleKeys.list(params),
    queryFn: () => axios.get(`/cycle/list-cycles?${queryString}`).then((r: any) => r.payload),
  });
};

export const useAddCycle = () => {
  const invalidate = useInvalidateCycleList();
  return useMutation({
    mutationFn: ({ pond_id, ...data }: { pond_id: string; name: string; start_date: string }) =>
      axios.post(`/cycle/add-cycle?pond_id=${pond_id}`, data).then((r: any) => r.payload),
    onSuccess: () => invalidate(),
  });
};

export const useEditCycle = () => {
  const invalidate = useInvalidateCycleList();
  return useMutation({
    mutationFn: ({ cycle_id, ...data }: { cycle_id: string; name: string; start_date: string; is_active: boolean }) =>
      axios.put(`/cycle/update-cycle?cycle_id=${cycle_id}`, data).then((r: any) => r.payload),
    onSuccess: () => invalidate(),
  });
};

export const useDeleteCycle = () => {
  const invalidate = useInvalidateCycleList();
  return useMutation({
    mutationFn: (cycle_id: string) =>
      axios.delete(`/cycle/delete-cycle?cycle_id=${cycle_id}`).then((r: any) => r.payload),
    onSuccess: () => invalidate(),
  });
};
