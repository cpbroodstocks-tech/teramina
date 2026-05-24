import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import PrintIcon from "@mui/icons-material/Print";
import { useFarmPLReport, useFarmYearPLReport } from "features/pl-report/queries";
import Error from "components/error";

const fmt = (n) => (n == null ? "—" : Number(n).toLocaleString("id-ID"));
const fmtIDR = (n) => (n == null ? "—" : `Rp ${fmt(n)}`);
const fmtPct = (n) => (n == null ? "—" : `${n}%`);

const Row = ({ label, value, bold, indent, highlight }) => (
  <Box
    sx={{
      display: "flex",
      justifyContent: "space-between",
      py: 0.5,
      pl: indent ? 3 : 0,
      bgcolor: highlight ? (highlight === "pos" ? "#e8f5e9" : highlight === "neg" ? "#fce4ec" : "#f5f5f5") : "transparent",
      borderRadius: 0.5,
    }}
  >
    <Typography variant="body2" fontWeight={bold ? 700 : 400}>{label}</Typography>
    <Typography variant="body2" fontWeight={bold ? 700 : 400}>{value}</Typography>
  </Box>
);

const SectionHeader = ({ children }) => (
  <Typography
    variant="caption"
    fontWeight={700}
    color="text.secondary"
    sx={{ display: "block", mt: 2.5, mb: 0.5, letterSpacing: 1, textTransform: "uppercase" }}
  >
    {children}
  </Typography>
);

const currentYear = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 5 }, (_, i) => currentYear - i);

const PLBody = ({ data, mode }) => {
  const netPos = data.net_profit_idr >= 0;
  const grossPos = data.gross_profit_idr >= 0;

  return (
    <Box sx={{ maxWidth: 760, mx: "auto" }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h5" fontWeight={700}>
          {mode === "year" ? "Annual " : ""}Farm Profit &amp; Loss Statement
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {data.farm_name}
          {data.farm_location ? ` · ${data.farm_location}` : ""}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {mode === "year"
            ? `Year: ${data.year}  ·  ${data.cycle_count} cycle(s) overlapping`
            : `${data.cycle_count} active cycle${data.cycle_count !== 1 ? "s" : ""}  ·  Currency: ${data.currency}`}
        </Typography>
        {mode === "year" && (
          <Typography variant="caption" color="text.secondary" display="block">
            {data.note}
          </Typography>
        )}
        <Typography variant="caption" color="text.secondary" display="block">
          Generated: {new Date(data.generated_at).toLocaleString("id-ID")}
        </Typography>
      </Box>

      <Divider />

      <SectionHeader>Revenue</SectionHeader>
      <Row bold label="Total Revenue" value={fmtIDR(data.total_revenue_idr)} />

      <Divider sx={{ mt: 1 }} />

      <SectionHeader>Cost of Production (COGS)</SectionHeader>
      {data.cost_seed_idr > 0 && <Row indent label="Seed / Fry" value={fmtIDR(data.cost_seed_idr)} />}
      <Row indent label="Feed" value={fmtIDR(data.cost_feed_idr)} />
      <Row indent label="Harvest Operations" value={fmtIDR(data.cost_harvest_idr)} />
      <Row bold label="Total COGS" value={fmtIDR(data.total_cogs_idr)} />
      <Row bold highlight={grossPos ? "pos" : "neg"} label={`Gross Profit (${fmtPct(data.gross_margin_pct)})`} value={fmtIDR(data.gross_profit_idr)} />

      <Divider sx={{ mt: 1 }} />

      <SectionHeader>Operating Expenses</SectionHeader>
      <Row indent label="Labor" value={fmtIDR(data.cost_labor_idr)} />
      <Row indent label="Energy" value={fmtIDR(data.cost_energy_idr)} />
      <Row indent label="Probiotics &amp; Treatment" value={fmtIDR(data.cost_probiotics_idr)} />
      <Row indent label="Bonus" value={fmtIDR(data.cost_bonus_idr)} />
      <Row indent label="Other" value={fmtIDR(data.cost_other_idr)} />
      <Row bold label="Total Operating Expenses" value={fmtIDR(data.total_opex_idr)} />

      <Divider sx={{ mt: 1 }} />

      <Box sx={{ mt: 1 }}>
        <Row bold label="Total Cost" value={fmtIDR(data.total_cost_idr)} />
        <Row bold highlight={netPos ? "pos" : "neg"} label={`Net Profit (${fmtPct(data.net_margin_pct)})`} value={fmtIDR(data.net_profit_idr)} />
      </Box>

      <Divider sx={{ mt: 2, mb: 2 }} />

      <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>
        Aggregated KPIs (weighted average)
      </Typography>
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1.5 }}>
        {[
          ["Total Harvest", `${data.kpi.total_harvest_kg} kg`],
          ["FCR", data.kpi.fcr],
          ["Avg SR", fmtPct(data.kpi.survival_rate_pct)],
          ["Cost / kg", fmtIDR(data.kpi.cost_per_kg_idr)],
          ["Revenue / kg", fmtIDR(data.kpi.revenue_per_kg_idr)],
          ...(data.kpi.final_abw_g != null ? [["Avg ABW", `${data.kpi.final_abw_g} g`]] : []),
        ].map(([label, val]) => (
          <Box key={label} sx={{ border: "1px solid #e0e0e0", borderRadius: 1, p: 1.5, minWidth: 120 }}>
            <Typography variant="caption" color="text.secondary" display="block">{label}</Typography>
            <Typography variant="subtitle1" fontWeight={700}>{val}</Typography>
          </Box>
        ))}
      </Box>

      <Divider sx={{ mt: 3, mb: 2 }} />

      {mode === "year" && data.per_cycle?.length > 0 && (
        <>
          <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>Per-Cycle Breakdown (pro-rated)</Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Pond</strong></TableCell>
                  <TableCell><strong>Cycle</strong></TableCell>
                  <TableCell><strong>Dates</strong></TableCell>
                  <TableCell align="right"><strong>Proration</strong></TableCell>
                  <TableCell align="right"><strong>Revenue (IDR)</strong></TableCell>
                  <TableCell align="right"><strong>Cost (IDR)</strong></TableCell>
                  <TableCell align="right"><strong>Net Profit (IDR)</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.per_cycle.map((p, i) => (
                  <TableRow key={i}>
                    <TableCell>{p.pond_name}</TableCell>
                    <TableCell>{p.cycle_name}</TableCell>
                    <TableCell>
                      <Typography variant="caption">{p.cycle_start} → {p.cycle_end}</Typography>
                    </TableCell>
                    <TableCell align="right">{p.proration_pct}%</TableCell>
                    <TableCell align="right">{fmtIDR(p.prorated_revenue_idr)}</TableCell>
                    <TableCell align="right">{fmtIDR(p.prorated_cost_idr)}</TableCell>
                    <TableCell align="right" sx={{ color: p.prorated_net_profit_idr >= 0 ? "success.main" : "error.main" }}>
                      {fmtIDR(p.prorated_net_profit_idr)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}

      {mode === "active" && data.per_pond?.length > 0 && (
        <>
          <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>Per-Pond Breakdown</Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Pond</strong></TableCell>
                  <TableCell><strong>Cycle</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell align="right"><strong>Revenue (IDR)</strong></TableCell>
                  <TableCell align="right"><strong>Cost (IDR)</strong></TableCell>
                  <TableCell align="right"><strong>Net Profit (IDR)</strong></TableCell>
                  <TableCell align="right"><strong>Margin</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.per_pond.map((p, i) => (
                  <TableRow key={i}>
                    <TableCell>{p.pond_name}</TableCell>
                    <TableCell>
                      {p.cycle_name}{" "}
                      <Typography variant="caption" color="text.secondary">({p.doc_range})</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={p.is_active ? "Active" : "Done"} size="small" color={p.is_active ? "info" : "default"} />
                    </TableCell>
                    <TableCell align="right">{fmtIDR(p.total_revenue_idr)}</TableCell>
                    <TableCell align="right">{fmtIDR(p.total_cost_idr)}</TableCell>
                    <TableCell align="right" sx={{ color: p.net_profit_idr >= 0 ? "success.main" : "error.main" }}>
                      {fmtIDR(p.net_profit_idr)}
                    </TableCell>
                    <TableCell align="right">{fmtPct(p.net_margin_pct)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  );
};

const FarmPLReportPage = () => {
  const { farm_id } = useParams();
  const [mode, setMode] = useState("active");
  const [year, setYear] = useState(currentYear);

  const { data: activeData, isLoading: activeLoading, isError: activeError } = useFarmPLReport(farm_id);
  const { data: yearData, isLoading: yearLoading, isError: yearError } = useFarmYearPLReport(farm_id, year);

  const isLoading = mode === "active" ? activeLoading : yearLoading;
  const isError = mode === "active" ? activeError : yearError;
  const data = mode === "active" ? activeData : yearData;

  return (
    <Box>
      <style>{`
        @media print {
          nav, aside, header, .MuiDrawer-root, .MuiAppBar-root { display: none !important; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
        }
      `}</style>

      <Box className="no-print" sx={{ display: "flex", alignItems: "center", gap: 2, justifyContent: "flex-end", mb: 2, flexWrap: "wrap" }}>
        <ToggleButtonGroup
          value={mode}
          exclusive
          size="small"
          onChange={(_, v) => { if (v) setMode(v); }}
        >
          <ToggleButton value="active">Active Cycles</ToggleButton>
          <ToggleButton value="year">Year View</ToggleButton>
        </ToggleButtonGroup>

        {mode === "year" && (
          <Select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            size="small"
            sx={{ minWidth: 100 }}
          >
            {YEAR_OPTIONS.map((y) => (
              <MenuItem key={y} value={y}>{y}</MenuItem>
            ))}
          </Select>
        )}

        <Button variant="outlined" startIcon={<PrintIcon />} onClick={() => window.print()} size="small">
          Print
        </Button>
      </Box>

      {isLoading && <Box sx={{ display: "flex", justifyContent: "center", pt: 6 }}><CircularProgress /></Box>}
      {!isLoading && (isError || !data) && <Error />}
      {!isLoading && data && <PLBody data={data} mode={mode} />}
    </Box>
  );
};

export default FarmPLReportPage;
