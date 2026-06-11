import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { axios } from "helper/axios";

export const pondKeys = {
  list: (params: Record<string, string>) => ["ponds", params] as const,
};

export const useInvalidatePondList = () => {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["ponds"] });
    queryClient.invalidateQueries({ queryKey: ["farm-hierarchy"] });
  };
};

export const usePondList = () => {
  const params = useParams() as Record<string, string>;
  const queryString = new URLSearchParams(params).toString();
  return useQuery({
    queryKey: pondKeys.list(params),
    queryFn: () => axios.get(`/pond/list-pond?${queryString}`).then((r: any) => r.payload),
  });
};

export const useAddPond = () => {
  const invalidate = useInvalidatePondList();
  return useMutation({
    mutationFn: ({ farm_id, ...data }: { farm_id: string; name: string; size: string; pond_construction: string; pond_shape: string }) =>
      axios.post(`/pond/add-pond?farm_id=${farm_id}`, data).then((r: any) => r.payload),
    onSuccess: () => invalidate(),
  });
};

export const useEditPond = () => {
  const invalidate = useInvalidatePondList();
  return useMutation({
    mutationFn: ({ pond_id, ...data }: { pond_id: string; name: string; size: string; pond_construction: string; pond_shape: string; is_active: boolean }) =>
      axios.put(`/pond/update-pond?pond_id=${pond_id}`, data).then((r: any) => r.payload),
    onSuccess: () => invalidate(),
  });
};

export const useDeletePond = () => {
  const invalidate = useInvalidatePondList();
  return useMutation({
    mutationFn: (pond_id: string) =>
      axios.delete(`/pond/delete-pond?pond_id=${pond_id}`).then((r: any) => r.payload),
    onSuccess: () => invalidate(),
  });
};

export const useDownloadPLReport = () =>
  useMutation({
    mutationFn: (farm_id: string) =>
      axios
        .get(`/cost/download-pl-report?farm_id=${farm_id}`, { responseType: "blob" })
        .then((r: any) => r as Blob),
  });
