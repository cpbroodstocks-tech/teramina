import { FormControl, InputLabel, MenuItem, Select, Stack } from "@mui/material";
import { useFarmHierarchy } from "features/farm/queries";
import { useDashboardContextStore } from "store/dashboard-context.store";

const ContextSelector = () => {
  const { data: farms = [] } = useFarmHierarchy();
  const context = useDashboardContextStore();
  const selectedFarm = farms.find((farm) => farm.id === context.farm_id) || farms[0];
  const ponds = selectedFarm?.ponds || [];
  const selectedPond = ponds.find((pond) => pond.id === context.pond_id) || ponds[0];
  const cycles = selectedPond?.cycles || [];

  if (!selectedFarm) return null;

  const setContextAndRefresh = (next: Parameters<typeof context.setContext>[0]) => {
    context.setContext(next);
    window.location.reload();
  };

  return (
    <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ flex: 1 }}>
      <FormControl size="small" sx={{ minWidth: 180 }}>
        <InputLabel>Farm</InputLabel>
        <Select
          label="Farm"
          value={selectedFarm.id}
          onChange={(event) => {
            const farm = farms.find((item) => item.id === event.target.value);
            const pond = farm?.ponds[0];
            const cycle = pond?.cycles.find((item) => item.dashboard_ready) || pond?.cycles[0];
            setContextAndRefresh({
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
      <FormControl size="small" sx={{ minWidth: 180 }} disabled={!ponds.length}>
        <InputLabel>Pond</InputLabel>
        <Select
          label="Pond"
          value={selectedPond?.id || ""}
          onChange={(event) => {
            const pond = ponds.find((item) => item.id === event.target.value);
            const cycle = pond?.cycles.find((item) => item.dashboard_ready) || pond?.cycles[0];
            setContextAndRefresh({
              pond_id: pond?.id || "",
              pond_name: pond?.name || "",
              cycle_id: cycle?.id || "",
              cycle_name: cycle?.name || "",
            });
          }}
        >
          {ponds.map((pond) => <MenuItem key={pond.id} value={pond.id}>{pond.name}</MenuItem>)}
        </Select>
      </FormControl>
      <FormControl size="small" sx={{ minWidth: 210 }} disabled={!cycles.length}>
        <InputLabel>Cycle</InputLabel>
        <Select
          label="Cycle"
          value={cycles.some((cycle) => cycle.id === context.cycle_id) ? context.cycle_id : cycles[0]?.id || ""}
          onChange={(event) => {
            const cycle = cycles.find((item) => item.id === event.target.value);
            setContextAndRefresh({ cycle_id: cycle?.id || "", cycle_name: cycle?.name || "" });
          }}
        >
          {cycles.map((cycle) => (
            <MenuItem key={cycle.id} value={cycle.id}>
              {cycle.name}{cycle.dashboard_ready ? "" : " (not ready)"}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Stack>
  );
};

export default ContextSelector;
