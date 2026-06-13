import { useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  FormControlLabel,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Stack,
  Switch,
  Tooltip,
  Typography,
} from "@mui/material";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import RestoreIcon from "@mui/icons-material/Restore";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import { useNavigate } from "react-router-dom";
import Loader from "components/loader";
import Error from "components/error";
import ModalFarmAdd from "features/farm/modal-add-farm";
import {
  CycleHierarchyItem,
  FarmHierarchyItem,
  PondHierarchyItem,
  useArchiveCycle,
  useArchiveFarm,
  useArchivePond,
  useFarmHierarchy,
  useRestoreCycle,
  useRestoreFarm,
  useRestorePond,
  useSetActiveCycle,
} from "features/farm/queries";
import { useDashboardContextStore } from "store/dashboard-context.store";

type Selection =
  | { type: "farm"; farm: FarmHierarchyItem }
  | { type: "pond"; farm: FarmHierarchyItem; pond: PondHierarchyItem }
  | { type: "cycle"; farm: FarmHierarchyItem; pond: PondHierarchyItem; cycle: CycleHierarchyItem };

const StatusChips = ({ archived, ready, active }: { archived?: boolean; ready?: boolean; active?: boolean }) => (
  <Stack direction="row" spacing={0.75} useFlexGap sx={{ flexWrap: "wrap" }}>
    {archived && <Chip size="small" label="Archived" />}
    {active && <Chip size="small" color="success" label="Active cycle" />}
    {ready === true && <Chip size="small" color="primary" variant="outlined" label="Dashboard ready" />}
    {ready === false && <Chip size="small" color="warning" variant="outlined" label="Not dashboard ready" />}
  </Stack>
);

const FarmManagement = () => {
  const navigate = useNavigate();
  const [includeArchived, setIncludeArchived] = useState(false);
  const [selectionKey, setSelectionKey] = useState("");
  const { data: farms = [], isLoading, isError } = useFarmHierarchy(includeArchived);
  const context = useDashboardContextStore();
  const archiveFarm = useArchiveFarm();
  const restoreFarm = useRestoreFarm();
  const archivePond = useArchivePond();
  const restorePond = useRestorePond();
  const archiveCycle = useArchiveCycle();
  const restoreCycle = useRestoreCycle();
  const setActiveCycle = useSetActiveCycle();

  const selections = useMemo(() => {
    const items: Record<string, Selection> = {};
    farms.forEach((farm) => {
      items[`farm:${farm.id}`] = { type: "farm", farm };
      farm.ponds.forEach((pond) => {
        items[`pond:${pond.id}`] = { type: "pond", farm, pond };
        pond.cycles.forEach((cycle) => {
          items[`cycle:${cycle.id}`] = { type: "cycle", farm, pond, cycle };
        });
      });
    });
    return items;
  }, [farms]);

  const defaultKey = context.cycle_id && selections[`cycle:${context.cycle_id}`]
    ? `cycle:${context.cycle_id}`
    : context.pond_id && selections[`pond:${context.pond_id}`]
      ? `pond:${context.pond_id}`
      : context.farm_id && selections[`farm:${context.farm_id}`]
        ? `farm:${context.farm_id}`
        : farms[0] ? `farm:${farms[0].id}` : "";
  const selection = selections[selectionKey] || selections[defaultKey];

  const select = (key: string) => {
    const next = selections[key];
    setSelectionKey(key);
    if (!next) return;
    if (next.type === "farm") {
      context.setContext({ farm_id: next.farm.id, farm_name: next.farm.name, pond_id: "", pond_name: "", cycle_id: "", cycle_name: "" });
    } else if (next.type === "pond") {
      context.setContext({
        farm_id: next.farm.id,
        farm_name: next.farm.name,
        pond_id: next.pond.id,
        pond_name: next.pond.name,
        cycle_id: "",
        cycle_name: "",
      });
    } else {
      context.setContext({
        farm_id: next.farm.id,
        farm_name: next.farm.name,
        pond_id: next.pond.id,
        pond_name: next.pond.name,
        cycle_id: next.cycle.id,
        cycle_name: next.cycle.name,
      });
    }
  };

  if (isLoading) return <Loader />;
  if (isError) return <Error />;

  const lifecycleAction = () => {
    if (!selection) return;
    if (!isArchived && !window.confirm(`Archive this ${selection.type}? Child records will be hidden from operational workflows.`)) return;
    if (selection.type === "farm") {
      (selection.farm.is_archived ? restoreFarm : archiveFarm).mutate(selection.farm.id);
    } else if (selection.type === "pond") {
      (selection.pond.is_archived ? restorePond : archivePond).mutate(selection.pond.id);
    } else {
      (selection.cycle.is_archived ? restoreCycle : archiveCycle).mutate(selection.cycle.id);
    }
    setSelectionKey("");
  };

  const isArchived = selection?.type === "farm"
    ? selection.farm.is_archived
    : selection?.type === "pond" ? selection.pond.is_archived : selection?.cycle.is_archived;

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: "column", md: "row" }} spacing={1} sx={{ justifyContent: "space-between", alignItems: { md: "center" } }}>
        <Box>
          <Typography variant="h2">Farm Management</Typography>
          <Typography color="text.secondary">Manage farm structure here. Use the operational dashboards to analyze selected cycles.</Typography>
        </Box>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <FormControlLabel
            control={<Switch checked={includeArchived} onChange={(event) => setIncludeArchived(event.target.checked)} />}
            label="Show archived"
          />
          <ModalFarmAdd />
        </Stack>
      </Stack>

      {!farms.length ? (
        <Alert severity="info">Create your first farm to start building the operating hierarchy.</Alert>
      ) : (
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "320px minmax(0, 1fr)" }, gap: 2, alignItems: "start" }}>
          <Paper variant="outlined" sx={{ maxHeight: "calc(100vh - 250px)", overflow: "auto" }}>
            <List dense disablePadding>
              {farms.map((farm) => (
                <Box key={farm.id}>
                  <ListItemButton selected={selection?.type === "farm" && selection.farm.id === farm.id} onClick={() => select(`farm:${farm.id}`)}>
                    <ListItemText primary={farm.name} secondary={`${farm.ponds.length} ponds${farm.is_archived ? " · archived" : ""}`} />
                    <ChevronRightIcon fontSize="small" />
                  </ListItemButton>
                  {farm.ponds.map((pond) => (
                    <Box key={pond.id}>
                      <ListItemButton
                        sx={{ pl: 4 }}
                        selected={selection?.type === "pond" && selection.pond.id === pond.id}
                        onClick={() => select(`pond:${pond.id}`)}
                      >
                        <ListItemText primary={pond.name} secondary={`${pond.cycles.length} cycles${pond.is_archived ? " · archived" : ""}`} />
                        <ChevronRightIcon fontSize="small" />
                      </ListItemButton>
                      {pond.cycles.map((cycle) => (
                        <ListItemButton
                          key={cycle.id}
                          sx={{ pl: 7 }}
                          selected={selection?.type === "cycle" && selection.cycle.id === cycle.id}
                          onClick={() => select(`cycle:${cycle.id}`)}
                        >
                          <ListItemText primary={cycle.name} secondary={cycle.dashboard_ready ? "Dashboard ready" : "Not ready"} />
                        </ListItemButton>
                      ))}
                    </Box>
                  ))}
                  <Divider />
                </Box>
              ))}
            </List>
          </Paper>

          {selection && (
            <Paper variant="outlined" sx={{ p: { xs: 2, md: 3 } }}>
              <Stack spacing={2}>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ justifyContent: "space-between" }}>
                  <Box>
                    <Typography variant="overline">{selection.type}</Typography>
                    <Typography variant="h3">
                      {selection.type === "farm" ? selection.farm.name : selection.type === "pond" ? selection.pond.name : selection.cycle.name}
                    </Typography>
                    <Typography color="text.secondary">
                      {selection.type === "farm"
                        ? selection.farm.location
                        : selection.type === "pond"
                          ? `${selection.farm.name} · ${selection.pond.size} m² · ${selection.pond.pond_construction}`
                          : `${selection.farm.name} › ${selection.pond.name} · started ${new Date(selection.cycle.start_date).toLocaleDateString()}`}
                    </Typography>
                  </Box>
                  <StatusChips
                    archived={isArchived}
                    ready={selection.type === "cycle" ? selection.cycle.dashboard_ready : undefined}
                    active={selection.type === "cycle" && selection.pond.active_cycle_id === selection.cycle.id}
                  />
                </Stack>

                <Divider />
                <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                  {selection.type === "farm" && (
                    <>
                      <Button variant="contained" endIcon={<OpenInNewIcon />} onClick={() => navigate(`/dashboard/pond/${selection.farm.id}`)}>Open ponds</Button>
                      <Button variant="outlined" onClick={() => navigate(`/dashboard/farm/pl-report/${selection.farm.id}`)}>Farm P&amp;L</Button>
                    </>
                  )}
                  {selection.type === "pond" && (
                    <>
                      <Button variant="contained" endIcon={<OpenInNewIcon />} onClick={() => navigate(`/dashboard/cycle/${selection.pond.id}`)}>Open cycles</Button>
                      <Button variant="outlined" onClick={() => navigate(`/dashboard/cost-data/${selection.farm.id}`)}>Cost data</Button>
                    </>
                  )}
                  {selection.type === "cycle" && (
                    <>
                      <Button variant="contained" endIcon={<OpenInNewIcon />} onClick={() => navigate(`/dashboard/cycle/detail/${selection.cycle.id}`)}>Open cycle details</Button>
                      <Button variant="outlined" onClick={() => navigate(`/dashboard/overview?farm_id=${selection.farm.id}&pond_id=${selection.pond.id}&cycle_id=${selection.cycle.id}`)}>Open overview</Button>
                      {selection.pond.active_cycle_id !== selection.cycle.id && !selection.cycle.is_archived && (
                        <Button
                          variant="outlined"
                          startIcon={<StarBorderIcon />}
                          onClick={() => setActiveCycle.mutate({ pondId: selection.pond.id, cycleId: selection.cycle.id })}
                        >
                          Set active cycle
                        </Button>
                      )}
                    </>
                  )}
                  <Tooltip title={isArchived ? "Restore" : "Archive"}>
                    <IconButton color={isArchived ? "primary" : "default"} onClick={lifecycleAction} aria-label={isArchived ? "Restore" : "Archive"}>
                      {isArchived ? <RestoreIcon /> : <ArchiveOutlinedIcon />}
                    </IconButton>
                  </Tooltip>
                </Stack>

                {selection.type === "farm" && <Typography>{selection.farm.ponds.length} ponds in this farm.</Typography>}
                {selection.type === "pond" && <Typography>{selection.pond.cycles.length} cycles in this pond.</Typography>}
                {selection.type === "cycle" && !selection.cycle.dashboard_ready && (
                  <Alert severity="warning">This cycle exists in Farm Management but does not yet contain the records required by operational dashboards.</Alert>
                )}
              </Stack>
            </Paper>
          )}
        </Box>
      )}
    </Stack>
  );
};

export default FarmManagement;
