import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  MenuItem,
  Select,
  Slider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Paper,
  FormControl,
  InputLabel,
} from "@mui/material";
import { MdExpandMore } from "react-icons/md";
import { useToastStore } from "store/toast.store";
import { useHarvestPresets, useSavedScenarios, useRunSimulation, useSaveScenario } from "widgets/harvest-simulator/queries";
import LineEcharts from "components/echarts/line";

const SCENARIO_TYPES = ["date_range", "partial", "price_sensitivity"];

const fmt = (n) => (n != null ? Number(n).toLocaleString("id-ID") : "—");

const HarvestSimulator = () => {
  const { cycle_id } = useParams();
  const { setToast } = useToastStore();

  const [scenarioType, setScenarioType] = useState("date_range");
  const [params, setParams] = useState({
    doc_start: "",
    doc_end: "",
    step_days: 3,
    doc_target: "",
    partial_pct: 50,
  });
  const [results, setResults] = useState(null);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [saveName, setSaveName] = useState("");

  const { data: presets = [] } = useHarvestPresets(cycle_id);
  const { data: savedScenarios = [] } = useSavedScenarios(cycle_id);
  const { mutateAsync: runSimulation, isPending: running } = useRunSimulation(cycle_id);
  const { mutateAsync: saveScenario, isPending: saving } = useSaveScenario(cycle_id);

  const handleParamChange = (field, value) => {
    setParams((prev) => ({ ...prev, [field]: value }));
  };

  const buildScenario = () => {
    if (scenarioType === "date_range") {
      return {
        type: scenarioType,
        doc_start: Number(params.doc_start),
        doc_end: Number(params.doc_end),
        step_days: Number(params.step_days),
      };
    }
    if (scenarioType === "partial") {
      return {
        type: scenarioType,
        doc_partial: Number(params.doc_target),
        doc_final: Number(params.doc_target) + 21,
        partial_pct: params.partial_pct,
      };
    }
    // price_sensitivity
    return {
      type: scenarioType,
      doc_end: Number(params.doc_target),
    };
  };

  const handleRun = async () => {
    try {
      const result = await runSimulation([buildScenario()]);
      setResults(result);
    } catch {
      setToast({ open: true, variant: "error", text: "Simulation failed" });
    }
  };

  const handleSave = async () => {
    if (!saveName.trim()) return;
    try {
      await saveScenario({ name: saveName, params: buildScenario(), results: results?.results || [] });
      setSaveDialogOpen(false);
      setSaveName("");
      setToast({ open: true, variant: "success", text: "Scenario saved" });
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to save scenario" });
    }
  };

  const resultRows = results?.results || [];

  const buildChartOption = () => {
    if (!resultRows.length) return {};
    const labels = resultRows.map((r) => r.label || `DOC ${r.doc}`);
    const profits = resultRows.map((r) => r.gross_profit_idr);
    const biomasses = resultRows.map((r) => r.harvest_biomass_kg);
    return {
      tooltip: { trigger: "axis" },
      legend: { data: ["Profit (IDR)", "Biomass (kg)"] },
      xAxis: { type: "category", data: labels, axisLabel: { rotate: 25, fontSize: 10 } },
      yAxis: [
        { type: "value", name: "Profit (IDR)" },
        { type: "value", name: "Biomass (kg)" },
      ],
      series: [
        {
          name: "Profit (IDR)",
          type: "line",
          data: profits,
          itemStyle: { color: "#474DA4" },
        },
        {
          name: "Biomass (kg)",
          type: "line",
          yAxisIndex: 1,
          data: biomasses,
          itemStyle: { color: "#FBBC05" },
        },
      ],
    };
  };

  return (
    <Box style={{ padding: "16px 0" }}>
      <Typography variant="h5" style={{ marginBottom: 16, fontWeight: 600 }}>
        Harvest Scenario Simulator
      </Typography>

      <Grid container spacing={2}>
        {/* Left: Config panel */}
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Scenario Configuration
              </Typography>

              <FormControl fullWidth size="small" style={{ marginBottom: 16 }}>
                <InputLabel>Scenario Type</InputLabel>
                <Select
                  label="Scenario Type"
                  value={scenarioType}
                  onChange={(e) => setScenarioType(e.target.value)}
                >
                  {SCENARIO_TYPES.map((t) => (
                    <MenuItem key={t} value={t}>
                      {t.replace(/_/g, " ")}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {scenarioType === "date_range" && (
                <Box style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <TextField
                    label="DOC Start"
                    type="number"
                    size="small"
                    value={params.doc_start}
                    onChange={(e) => handleParamChange("doc_start", e.target.value)}
                  />
                  <TextField
                    label="DOC End"
                    type="number"
                    size="small"
                    value={params.doc_end}
                    onChange={(e) => handleParamChange("doc_end", e.target.value)}
                  />
                  <TextField
                    label="Step Days"
                    type="number"
                    size="small"
                    value={params.step_days}
                    onChange={(e) => handleParamChange("step_days", e.target.value)}
                  />
                </Box>
              )}

              {scenarioType === "partial" && (
                <Box style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <TextField
                    label="Partial Harvest DOC"
                    type="number"
                    size="small"
                    value={params.doc_target}
                    onChange={(e) => handleParamChange("doc_target", e.target.value)}
                  />
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      Partial % : {params.partial_pct}%
                    </Typography>
                    <Slider
                      min={10}
                      max={90}
                      value={params.partial_pct}
                      onChange={(_, v) => handleParamChange("partial_pct", v)}
                    />
                  </Box>
                </Box>
              )}

              {scenarioType === "price_sensitivity" && (
                <Box style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <TextField
                    label="Target DOC"
                    type="number"
                    size="small"
                    value={params.doc_target}
                    onChange={(e) => handleParamChange("doc_target", e.target.value)}
                  />
                  <Typography variant="caption" color="textSecondary">
                    Sweeps price ±20% around market rate at the target DOC.
                  </Typography>
                </Box>
              )}

              <Box style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Button
                  variant="contained"
                  onClick={handleRun}
                  disabled={running}
                >
                  {running ? <CircularProgress size={18} style={{ marginRight: 8 }} /> : null}
                  Run Simulation
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Preset quick-view */}
          {presets.length > 0 && (
            <Card style={{ marginTop: 12 }}>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom style={{ fontWeight: 600 }}>
                  Quick Presets
                </Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Scenario</TableCell>
                      <TableCell align="right">Profit (IDR)</TableCell>
                      <TableCell align="right">ABW (g)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {presets.map((p, i) => (
                      <TableRow key={i}>
                        <TableCell>{p.label}</TableCell>
                        <TableCell align="right">{fmt(p.gross_profit_idr)}</TableCell>
                        <TableCell align="right">{p.projected_abw_g ?? "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Right: Results */}
        <Grid item xs={12} md={7}>
          {results && (
            <Card>
              <CardContent>
                <Box style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <Typography variant="h6">Results</Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setSaveDialogOpen(true)}
                  >
                    Save Scenario
                  </Button>
                </Box>
                <LineEcharts
                  option={buildChartOption()}
                  inlineStyle={{ height: "280px" }}
                />
                {resultRows.length > 0 && (
                  <TableContainer component={Paper} style={{ marginTop: 16 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Label</TableCell>
                          <TableCell>DOC</TableCell>
                          <TableCell>ABW (g)</TableCell>
                          <TableCell>Biomass (kg)</TableCell>
                          <TableCell>Revenue</TableCell>
                          <TableCell>Cost</TableCell>
                          <TableCell>Profit</TableCell>
                          <TableCell>Margin %</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {resultRows.map((row, i) => (
                          <TableRow key={i}>
                            <TableCell>{row.label || "—"}</TableCell>
                            <TableCell>{row.doc}</TableCell>
                            <TableCell>{row.projected_abw_g}</TableCell>
                            <TableCell>{row.harvest_biomass_kg}</TableCell>
                            <TableCell>{fmt(row.gross_revenue_idr)}</TableCell>
                            <TableCell>{fmt(row.total_cost_idr)}</TableCell>
                            <TableCell>{fmt(row.gross_profit_idr)}</TableCell>
                            <TableCell>{row.profit_margin_pct}%</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Saved Scenarios */}
      {savedScenarios.length > 0 && (
        <Box style={{ marginTop: 16 }}>
          <Accordion>
            <AccordionSummary expandIcon={<MdExpandMore />}>
              <Typography variant="subtitle1">
                Saved Scenarios ({savedScenarios.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {savedScenarios.map((s, i) => (
                  <Box
                    key={i}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      padding: "8px 12px",
                      border: "1px solid #e0e0e0",
                      borderRadius: 8,
                    }}
                  >
                    <Typography variant="body2" style={{ flex: 1, fontWeight: 500 }}>
                      {s.name}
                    </Typography>
                    <Chip label={`${s.result_count} points`} size="small" />
                    <Typography variant="caption" color="textSecondary">
                      {s.created_at ? new Date(s.created_at).toLocaleDateString("id-ID") : "—"}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </AccordionDetails>
          </Accordion>
        </Box>
      )}

      {/* Save Dialog */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Save Scenario</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Scenario Name"
            size="small"
            value={saveName}
            onChange={(e) => setSaveName(e.target.value)}
            style={{ marginTop: 8 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={saving || !saveName.trim()}
          >
            {saving ? <CircularProgress size={18} /> : "Save"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HarvestSimulator;
