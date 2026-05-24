import { useParams } from "react-router-dom";
import { Box, Chip, CircularProgress, Divider, Typography } from "@mui/material";
import { usePublicPLReport } from "features/pl-report/queries";

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

const SharePage = () => {
  const { token } = useParams();
  const { data, isLoading, isError, error } = usePublicPLReport(token);

  if (isLoading) return <Box sx={{ display: "flex", justifyContent: "center", pt: 8 }}><CircularProgress /></Box>;

  if (isError || !data) {
    const msg = error?.response?.data?.message || "This link is invalid or has expired.";
    return (
      <Box sx={{ maxWidth: 480, mx: "auto", mt: 10, textAlign: "center" }}>
        <Typography variant="h6" gutterBottom>Link Unavailable</Typography>
        <Typography variant="body2" color="text.secondary">{msg}</Typography>
      </Box>
    );
  }

  const netPos = data.net_profit_idr >= 0;
  const grossPos = data.gross_profit_idr >= 0;

  return (
    <Box sx={{ maxWidth: 720, mx: "auto", px: 2, py: 4 }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h5" fontWeight={700}>Profit &amp; Loss Statement</Typography>
        <Typography variant="body2" color="text.secondary">
          {data.cycle_name} &nbsp;·&nbsp; {data.pond_name}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {data.doc_range} &nbsp;·&nbsp; Start: {data.start_date ?? "—"} &nbsp;·&nbsp; Currency: {data.currency}
        </Typography>
        {data.is_active && <Chip label="Active Cycle — Projected figures included" size="small" color="info" sx={{ mt: 0.5 }} />}
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.25 }}>
          Generated: {new Date(data.generated_at).toLocaleString("id-ID")}
        </Typography>
      </Box>

      <Divider />

      <SectionHeader>Revenue</SectionHeader>
      {data.harvest_events.map((evt) => (
        <Row
          key={evt.key}
          indent
          label={`${evt.harvest_no === data.harvest_events.length ? "Final" : `Partial ${evt.harvest_no}`} Harvest — DOC ${evt.doc} (${evt.biomass_kg} kg @ size ${evt.size_count_per_kg}/kg)`}
          value={fmtIDR(evt.revenue_idr)}
        />
      ))}
      {data.projected_remaining_idr != null && (
        <Row indent label="Remaining in pond (projected)" value={fmtIDR(data.projected_remaining_idr)} />
      )}
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

      <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>Key Performance Indicators</Typography>
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1.5 }}>
        {[
          ["Cycle Duration", `${data.kpi.doc} days`],
          ["Total Harvest", `${data.kpi.total_harvest_kg} kg`],
          ["Final ABW", `${data.kpi.final_abw_g} g`],
          ["Survival Rate", fmtPct(data.kpi.survival_rate_pct)],
          ["FCR", data.kpi.fcr],
          ["Cost / kg", fmtIDR(data.kpi.cost_per_kg_idr)],
          ["Revenue / kg", fmtIDR(data.kpi.revenue_per_kg_idr)],
          ["Break-even Price", fmtIDR(data.kpi.break_even_price_idr)],
        ].map(([label, val]) => (
          <Box key={label} sx={{ border: "1px solid #e0e0e0", borderRadius: 1, p: 1.5, minWidth: 120, flex: "1 1 120px" }}>
            <Typography variant="caption" color="text.secondary" display="block">{label}</Typography>
            <Typography variant="subtitle1" fontWeight={700}>{val}</Typography>
          </Box>
        ))}
      </Box>

      <Box sx={{ mt: 3, pt: 1.5, borderTop: "1px solid #e0e0e0" }}>
        <Typography variant="caption" color="text.secondary">
          Shared via Teramina. {data.is_active ? "* Projected figures are estimates." : "All figures are based on recorded data."}
        </Typography>
      </Box>
    </Box>
  );
};

export default SharePage;
