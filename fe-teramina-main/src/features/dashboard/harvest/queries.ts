import { useMutation } from "@tanstack/react-query";
import { axios } from "helper/axios";

export const useAddHarvestRecord = (cycle_id: string) =>
  useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      axios.post(`/harvest/add-harvest-record?cycle_id=${cycle_id}`, body).then((r: any) => r.payload),
  });

export const useCreateHarvestSimulation = (cycle_id: string) =>
  useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      axios
        .post(`/harvest/create-harvest-simulation?cycle_id=${cycle_id}`, body)
        .then((r: any) => r.payload),
  });
