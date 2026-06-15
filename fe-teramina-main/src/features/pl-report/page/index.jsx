import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  IconButton,
  Snackbar,
  Tooltip,
  Typography,
} from "@mui/material";
import PrintIcon from "@mui/icons-material/Print";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import TableChartIcon from "@mui/icons-material/TableChart";
import ShareIcon from "@mui/icons-material/Share";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import { usePLReport, usePLNarrative, useSharePLReport, downloadPLPdf, downloadPLExcel, downloadBankPdf } from "features/pl-report/queries";
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
      "@media print": { py: 0.25 },
    }}
  >
    <Typography variant="body2" fontWeight={bold ? 700 : 400}>
      {label}
    </Typography>
    <Typography variant="body2" fontWeight={bold ? 700 : 400}>
      {value}
    </Typography>
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

const KpiCard = ({ label, value, unit }) => (
  <Box
    sx={{
      border: "1px solid #e0e0e0",
      borderRadius: 1,
      p: 1.5,
      minWidth: 120,
      flex: "1 1 120px",
      "@media print": { border: "1px solid #ccc", p: 1 },
    }}
  >
    <Typography variant="caption" color="text.secondary" display="block">
      {label}
    </Typography>
    <Typography variant="subtitle1" fontWeight={700}>
      {value}
    </Typography>
    {unit && (
      <Typography variant="caption" color="text.secondary">
        {unit}
      </Typography>
    )}
  </Box>
);

const BenchmarkBar = ({ myValue, p25, p50, p75, lowerIsBetter }) => {
  const max = Math.max((p75 || 0) * 1.2, (myValue || 0) * 1.1) || 1;
  const pct = (v) => Math.min(100, ((v || 0) / max) * 100);
  const good = lowerIsBetter ? myValue <= p50 : myValue >= p50;

  return (
    <Box sx={{ mt: 0.75 }}>
      <Box sx={{ height: 10, bgcolor: "#e0e0e0", borderRadius: 5, position: "relative" }}>
        {[p25, p50, p75].map((v, i) => (
          <Box key={i} sx={{ position: "absolute", left: `${pct(v)}%`, top: -3, bottom: -3, width: 2, bgcolor: "#9e9e9e" }} />
        ))}
        <Box sx={{ position: "absolute", left: `${pct(myValue)}%`, top: -5, bottom: -5, width: 3, bgcolor: "#474DA4", borderRadius: 1 }} />
      </Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", mt: 0.25 }}>
        {[["p25", p25], ["p50", p50], ["p75", p75]].map(([lbl, v]) => (
          <Typography key={lbl} variant="caption" color="text.secondary">
            {lbl}: {v ?? "—"}
          </Typography>
        ))}
      </Box>
      <Chip
        label={good ? "Above Average" : "Below Average"}
        size="small"
        color={good ? "success" : "warning"}
        sx={{ mt: 0.5, height: 18, fontSize: 10 }}
      />
    </Box>
  );
};

const PLReportPage = () => {
  const { cycle_id } = useParams();
  const { data, isLoading, isError } = usePLReport(cycle_id);
  const { mutate: createShare, isPending: sharing } = useSharePLReport(cycle_id);
  const [snack, setSnack] = useState("");
  const [narrativeOpen, setNarrativeOpen] = useState(false);
  const { data: narrative, isLoading: narrativeLoading } = usePLNarrative(cycle_id, narrativeOpen);

  const handleShare = () => {
    createShare(undefined, {
      onSuccess: (payload) => {
        const url = `${window.location.origin}/share/${payload.token}`;
        navigator.clipboard.writeText(url).then(() => setSnack("Link copied to clipboard!"));
      },
      onError: () => setSnack("Failed to generate share link"),
    });
  };

  if (isLoading) return <Box sx={{ display: "flex", justifyContent: "center", pt: 6 }}><CircularProgress /></Box>;
  if (isError || !data) return <Error />;

  const netPos = data.net_profit_idr >= 0;
  const grossPos = data.gross_profit_idr >= 0;

  return (
    <Box>
      <style>{`
        @media print {
          nav, aside, header, [data-sidebar], [data-nav], .MuiDrawer-root, .MuiAppBar-root { display: none !important; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
          .print-page { max-width: 100% !important; margin: 0 !important; padding: 0 !important; }
        }
      `}</style>

      {/* Toolbar — hidden on print */}
      <Box className="no-print" sx={{ display: "flex", gap: 1, justifyContent: "flex-end", mb: 2, flexWrap: "wrap" }}>
        <Tooltip title="AI Narrative Summary">
          <IconButton
            size="small"
            onClick={() => setNarrativeOpen((v) => !v)}
            color={narrativeOpen ? "primary" : "default"}
            aria-label="Toggle AI narrative summary"
          >
            <AutoAwesomeIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Download PDF">
          <IconButton size="small" onClick={() => downloadPLPdf(cycle_id)} aria-label="Download P&L PDF">
            <PictureAsPdfIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Download Excel">
          <IconButton size="small" onClick={() => downloadPLExcel(cycle_id)} aria-label="Download P&L Excel">
            <TableChartIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Bank / Cooperative Format PDF">
          <IconButton size="small" onClick={() => downloadBankPdf(cycle_id)} aria-label="Download bank format PDF">
            <AccountBalanceIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Copy shareable link (7-day expiry)">
          <IconButton size="small" onClick={handleShare} disabled={sharing} aria-label="Copy shareable link">
            {sharing ? <CircularProgress size={16} /> : <ShareIcon fontSize="small" />}
          </IconButton>
        </Tooltip>
        <Button
          variant="outlined"
          startIcon={<PrintIcon />}
          onClick={() => window.print()}
          size="small"
        >
          Print
        </Button>
      </Box>

      {/* AI Narrative */}
      <Collapse in={narrativeOpen}>
        <Box sx={{ maxWidth: 720, mx: "auto", mb: 2, p: 2, bgcolor: "#f0f4ff", borderRadius: 2, border: "1px solid #c7d0f5" }}>
          <Typography variant="caption" fontWeight={700} color="primary" sx={{ display: "block", mb: 1, letterSpacing: 1, textTransform: "uppercase" }}>
            AI Summary
          </Typography>
          {narrativeLoading ? (
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <CircularProgress size={16} />
              <Typography variant="body2" color="text.secondary">Generating narrative…</Typography>
            </Box>
          ) : (
            <Typography variant="body2" sx={{ whiteSpace: "pre-line", lineHeight: 1.8 }}>
              {narrative ?? "No narrative available."}
            </Typography>
          )}
        </Box>
      </Collapse>
      <Snackbar
        open={!!snack}
        autoHideDuration={3000}
        onClose={() => setSnack("")}
        message={snack}
      />

      <Box className="print-page" sx={{ maxWidth: 720, mx: "auto" }}>
        {/* Header */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="h5" fontWeight={700}>
            Profit &amp; Loss Statement
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {data.cycle_name} &nbsp;·&nbsp; {data.pond_name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {data.doc_range} &nbsp;·&nbsp; Start: {data.start_date ?? "—"} &nbsp;·&nbsp; Currency: {data.currency}
          </Typography>
          {data.is_active && (
            <Chip label="Active Cycle — Projected figures included" size="small" color="info" sx={{ mt: 0.5 }} />
          )}
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.25 }}>
            Generated: {new Date(data.generated_at).toLocaleString("id-ID")}
          </Typography>
        </Box>

        <Divider />

        {/* Revenue */}
        <SectionHeader>Revenue</SectionHeader>
        {data.harvest_events.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ pl: 3 }}>
            No recorded harvest events
          </Typography>
        )}
        {data.harvest_events.map((evt) => (
          <Row
            key={evt.key}
            indent
            label={`${evt.harvest_no === data.harvest_events.length ? "Final" : `Partial ${evt.harvest_no}`} Harvest — DOC ${evt.doc} (${evt.biomass_kg} kg @ size ${evt.size_count_per_kg}/kg)`}
            value={fmtIDR(evt.revenue_idr)}
          />
        ))}
        {data.projected_remaining_idr != null && (
          <Row
            indent
            label="Remaining in pond (projected, current price)"
            value={fmtIDR(data.projected_remaining_idr)}
          />
        )}
        <Row bold label="Total Revenue" value={fmtIDR(data.total_revenue_idr)} />

        <Divider sx={{ mt: 1 }} />

        {/* COGS */}
        <SectionHeader>Cost of Production (COGS)</SectionHeader>
        {data.cost_seed_idr > 0 && <Row indent label="Seed / Fry" value={fmtIDR(data.cost_seed_idr)} />}
        <Row indent label="Feed" value={fmtIDR(data.cost_feed_idr)} />
        <Row indent label="Harvest Operations" value={fmtIDR(data.cost_harvest_idr)} />
        <Row bold label="Total COGS" value={fmtIDR(data.total_cogs_idr)} />
        <Row
          bold
          highlight={grossPos ? "pos" : "neg"}
          label={`Gross Profit  (${fmtPct(data.gross_margin_pct)})`}
          value={fmtIDR(data.gross_profit_idr)}
        />

        <Divider sx={{ mt: 1 }} />

        {/* OpEx */}
        <SectionHeader>Operating Expenses</SectionHeader>
        <Row indent label="Labor" value={fmtIDR(data.cost_labor_idr)} />
        <Row indent label="Energy" value={fmtIDR(data.cost_energy_idr)} />
        <Row indent label="Probiotics &amp; Treatment" value={fmtIDR(data.cost_probiotics_idr)} />
        <Row indent label="Bonus" value={fmtIDR(data.cost_bonus_idr)} />
        <Row indent label="Other" value={fmtIDR(data.cost_other_idr)} />
        <Row bold label="Total Operating Expenses" value={fmtIDR(data.total_opex_idr)} />

        <Divider sx={{ mt: 1 }} />

        {/* Net */}
        <Box sx={{ mt: 1 }}>
          <Row bold label="Total Cost" value={fmtIDR(data.total_cost_idr)} />
          <Row
            bold
            highlight={netPos ? "pos" : "neg"}
            label={`Net Profit  (${fmtPct(data.net_margin_pct)})`}
            value={fmtIDR(data.net_profit_idr)}
          />
        </Box>

        <Divider sx={{ mt: 1.5, mb: 2 }} />

        {/* KPIs */}
        <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>
          Key Performance Indicators
        </Typography>
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1.5 }}>
          <KpiCard label="Cycle Duration" value={data.kpi.doc} unit="days" />
          <KpiCard label="Total Harvest" value={`${data.kpi.total_harvest_kg} kg`} />
          <KpiCard label="Final ABW" value={`${data.kpi.final_abw_g} g`} />
          <KpiCard label="Survival Rate" value={fmtPct(data.kpi.survival_rate_pct)} />
          <KpiCard label="FCR" value={data.kpi.fcr} />
          <KpiCard label="Cost / kg" value={fmtIDR(data.kpi.cost_per_kg_idr)} />
          <KpiCard label="Revenue / kg" value={fmtIDR(data.kpi.revenue_per_kg_idr)} />
          <KpiCard label="Break-even Price" value={fmtIDR(data.kpi.break_even_price_idr)} unit="/ kg" />
        </Box>

        {/* Benchmark */}
        {data.benchmark_available && data.benchmark.length > 0 && (
          <>
            <Divider sx={{ mt: 3, mb: 2 }} />
            <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1.5 }}>
              Peer Benchmark Comparison
            </Typography>
            <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 1.5 }}>
              {data.benchmark.map((b) => (
                <Box key={b.metric} sx={{ border: "1px solid #e0e0e0", borderRadius: 1, p: 1.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    {b.metric} {b.unit ? `(${b.unit})` : ""}
                  </Typography>
                  <Typography variant="subtitle2" fontWeight={700}>
                    {b.your_value}
                  </Typography>
                  <BenchmarkBar
                    myValue={b.your_value}
                    p25={b.peer_p25}
                    p50={b.peer_p50}
                    p75={b.peer_p75}
                    lowerIsBetter={b.lower_is_better}
                  />
                </Box>
              ))}
            </Box>
          </>
        )}

        <Box sx={{ mt: 3, pt: 1.5, borderTop: "1px solid #e0e0e0" }}>
          <Typography variant="caption" color="text.secondary">
            {data.is_active
              ? "* Projected figures are estimates based on current biomass value and market price. Actual results may vary."
              : "All figures are based on recorded harvest and operational data."}
            &nbsp; Generated by Teramina.
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default PLReportPage;
