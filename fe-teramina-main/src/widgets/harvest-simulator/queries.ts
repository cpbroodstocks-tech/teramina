import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { axios } from "helper/axios";

export const harvestSimulatorKeys = {
  presets: (cycle_id: string) => ["harvest-presets", cycle_id] as const,
  saved: (cycle_id: string) => ["harvest-saved", cycle_id] as const,
};

export const useHarvestPresets = (cycle_id: string) =>
  useQuery({
    queryKey: harvestSimulatorKeys.presets(cycle_id),
    queryFn: () =>
      axios.get("/harvest/simulate/presets", { params: { cycle_id } }).then((r: any) => r?.payload?.presets ?? []),
    enabled: !!cycle_id,
  });

export const useSavedScenarios = (cycle_id: string) =>
  useQuery({
    queryKey: harvestSimulatorKeys.saved(cycle_id),
    queryFn: () =>
      axios.get("/harvest/simulate/saved", { params: { cycle_id } }).then((r: any) => r?.payload?.scenarios ?? []),
    enabled: !!cycle_id,
  });

export const useRunSimulation = (cycle_id: string) =>
  useMutation({
    mutationFn: (scenarios: unknown[]) =>
      axios.post("/harvest/simulate", { scenarios }, { params: { cycle_id } }).then((r: any) => r?.payload ?? null),
  });

export const useSaveScenario = (cycle_id: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; params: unknown; results: unknown[] }) =>
      axios.post("/harvest/simulate/save", payload, { params: { cycle_id } }).then((r: any) => r.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: harvestSimulatorKeys.saved(cycle_id) }),
  });
};
