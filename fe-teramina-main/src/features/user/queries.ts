import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { axios } from "helper/axios";

export const userKeys = {
  profile: ["user-profile"] as const,
};

export const useUserProfile = () =>
  useQuery({
    queryKey: userKeys.profile,
    queryFn: () => axios.get("/user/get-profile").then((r: any) => r.payload),
  });

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) =>
      axios
        .post("/user/update-profile", formData, { headers: { "Content-Type": "multipart/form-data" } })
        .then((r: any) => r.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.profile }),
  });
};

export const useUploadCostData = () =>
  useMutation({
    mutationFn: ({
      farm_id,
      start_date,
      end_date,
      file,
    }: {
      farm_id: string;
      start_date: string;
      end_date: string;
      file: File;
    }) => {
      const formData = new FormData();
      formData.append("file", file);
      return axios
        .post("/cost/add-single-cost-data", formData, {
          params: { farm_id, start_date, end_date },
          headers: { "Content-Type": "multipart/form-data" },
        })
        .then((r: any) => r.payload);
    },
  });
