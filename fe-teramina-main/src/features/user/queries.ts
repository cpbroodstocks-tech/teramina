import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { axios } from "helper/axios";

export const userKeys = {
  profile: ["user-profile"] as const,
  dataStatus: ["user-data-status"] as const,
  adminAccessRequests: ["admin-access-requests"] as const,
};

export const useUserProfile = () =>
  useQuery({
    queryKey: userKeys.profile,
    queryFn: fetchUserProfile,
  });

export const verifyFirebaseUser = (token: string) =>
  axios.post("/user/firebase-verify-user", { token }).then((r: any) => r.payload);

export const fetchUserProfile = () => axios.get("/user/get-profile").then((r: any) => r.payload);

export const registerFcmToken = (token: string) => axios.post("/user/fcm-token", { token });

export const requestBetaAccess = (email: string, source = "landing") =>
  axios.post("/user/access-requests", { email, source }).then((r: any) => r.payload);

export const useAdminAccessRequests = (enabled = true) =>
  useQuery({
    queryKey: userKeys.adminAccessRequests,
    queryFn: () => axios.get("/user/admin/access-requests").then((r: any) => r?.payload?.requests ?? []),
    enabled,
  });

export const useUpdateAdminAccessRequest = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ requestId, status }: { requestId: string; status: "approved" | "rejected" }) =>
      axios.patch(`/user/admin/access-requests/${requestId}`, { status }).then((r: any) => r?.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.adminAccessRequests }),
  });
};

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

export const useUserDataStatus = () =>
  useQuery({
    queryKey: userKeys.dataStatus,
    queryFn: () => axios.get("/user/user-data-status").then((r: any) => r?.payload?.is_there_data),
  });
