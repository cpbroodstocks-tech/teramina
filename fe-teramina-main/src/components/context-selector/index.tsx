import { useEffect } from "react";
import { FormControl, InputLabel, MenuItem, Select, Stack } from "@mui/material";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { trackDemoEvent } from "features/demo-experience/analytics";
import { useFarmHierarchy } from "features/farm/queries";
import { useDashboardContextStore } from "store/dashboard-context.store";

type ContextLevel = "farm" | "pond" | "cycle";

const ContextSelector = ({ level = "cycle" }: { level?: ContextLevel }) => {
  const { t } = useTranslation();
  const { data: farms = [] } = useFarmHierarchy();
  const context = useDashboardContextStore();
  const queryClient = useQueryClient();
  const selectedFarm = farms.find((farm) => farm.id === context.farm_id) || farms[0];
  const ponds = selectedFarm?.ponds || [];
  const selectedPond = ponds.find((pond) => pond.id === context.pond_id)
    || ponds.find((pond) => pond.cycles.some((cycle) => cycle.dashboard_ready))
    || ponds[0];
  const cycles = selectedPond?.cycles || [];
  const selectedCycle = cycles.find((cycle) => cycle.id === context.cycle_id)
    || cycles.find((cycle) => cycle.dashboard_ready)
    || cycles[0];

  useEffect(() => {
    if (!selectedFarm) return;
    const resolved = {
      farm_id: selectedFarm.id,
      farm_name: selectedFarm.name,
      pond_id: selectedPond?.id || "",
      pond_name: selectedPond?.name || "",
      cycle_id: selectedCycle?.id || "",
      cycle_name: selectedCycle?.name || "",
    };
    if (
      resolved.farm_id !== context.farm_id
      || resolved.pond_id !== context.pond_id
      || resolved.cycle_id !== context.cycle_id
      || resolved.farm_name !== context.farm_name
      || resolved.pond_name !== context.pond_name
      || resolved.cycle_name !== context.cycle_name
    ) {
      context.setContext(resolved);
    }
  }, [
    selectedFarm?.id,
    selectedFarm?.name,
    selectedPond?.id,
    selectedPond?.name,
    selectedCycle?.id,
    selectedCycle?.name,
  ]);

  if (!selectedFarm) return null;

  const setDashboardContext = (next: Parameters<typeof context.setContext>[0]) => {
    context.setContext(next);
    const scenario = farms
      .flatMap((farm) => farm.ponds)
      .find((pond) => pond.id === next.pond_id)?.demo_scenario;
    if (scenario) {
      trackDemoEvent("demo_context_selected", { scenario }).catch(() => undefined);
    }
    queryClient.invalidateQueries();
  };

  return (
    <Stack
      direction={{ xs: "column", lg: "row" }}
      spacing={1}
      sx={{ flex: 1, minWidth: 0 }}
      aria-label={t("OPERATIONAL_CONTEXT")}
    >
      <FormControl size="small" sx={{ minWidth: { lg: 180 }, flex: "1 1 180px" }}>
        <InputLabel>{t("FARM")}</InputLabel>
        <Select
          label={t("FARM")}
          value={selectedFarm.id}
          onChange={(event) => {
            const farm = farms.find((item) => item.id === event.target.value);
            const pond = farm?.ponds[0];
            const cycle = pond?.cycles.find((item) => item.dashboard_ready) || pond?.cycles[0];
            setDashboardContext({
              farm_id: farm?.id || "",
              farm_name: farm?.name || "",
              pond_id: pond?.id || "",
              pond_name: pond?.name || "",
              cycle_id: cycle?.id || "",
              cycle_name: cycle?.name || "",
            });
          }}
        >
          {farms.map((farm) => <MenuItem key={farm.id} value={farm.id}>{farm.name}</MenuItem>)}
        </Select>
      </FormControl>
      {level !== "farm" && <FormControl size="small" sx={{ minWidth: { lg: 180 }, flex: "1 1 180px" }} disabled={!ponds.length}>
        <InputLabel>{t("POND")}</InputLabel>
        <Select
          label={t("POND")}
          value={selectedPond?.id || ""}
          onChange={(event) => {
            const pond = ponds.find((item) => item.id === event.target.value);
            const cycle = pond?.cycles.find((item) => item.dashboard_ready) || pond?.cycles[0];
            setDashboardContext({
              pond_id: pond?.id || "",
              pond_name: pond?.name || "",
              cycle_id: cycle?.id || "",
              cycle_name: cycle?.name || "",
            });
          }}
        >
          {ponds.map((pond) => <MenuItem key={pond.id} value={pond.id}>{pond.name}</MenuItem>)}
        </Select>
      </FormControl>}
      {level === "cycle" && <FormControl size="small" sx={{ minWidth: { lg: 210 }, flex: "1 1 210px" }} disabled={!cycles.length}>
        <InputLabel>{t("CYCLE")}</InputLabel>
        <Select
          label={t("CYCLE")}
          value={selectedCycle?.id || ""}
          onChange={(event) => {
            const cycle = cycles.find((item) => item.id === event.target.value);
            setDashboardContext({ cycle_id: cycle?.id || "", cycle_name: cycle?.name || "" });
          }}
        >
          {cycles.map((cycle) => (
            <MenuItem key={cycle.id} value={cycle.id}>
              {cycle.name}{cycle.dashboard_ready ? "" : ` (${t("NOT_READY")})`}
            </MenuItem>
          ))}
        </Select>
      </FormControl>}
    </Stack>
  );
};

export default ContextSelector;
