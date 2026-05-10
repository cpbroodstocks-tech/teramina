import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Box, Breadcrumbs, Button, IconButton, Tab, Tabs, Tooltip, Typography } from "@mui/material";
import BarChartIcon from "@mui/icons-material/BarChart";
import { SiGooglesheets } from "react-icons/si";
import Loader from "components/loader";
import PopulateList from "features/cycle-detail/populate-list";
import Error from "components/error";
import { useCycleDataList } from "features/cycle-data/queries";
import AiInsights from "features/cycle-detail/ai-insights";
import FeedingRecommendation from "features/cycle-detail/feeding-recommendation";
import BenchmarkSection from "features/cycle-detail/benchmark";
import GoogleSheets from "features/cycle-detail/google-sheets";
import DataQuality from "features/cycle-detail/data-quality";

const PopulateContent = () => {
  const { data, isLoading, isError } = useCycleDataList();

  if (isLoading) return <Loader />;
  if (isError) return <Error />;
  return <PopulateList data={data} />;
};

const CycleDetail = () => {
  const [tab, setTab] = useState(0);
  const [sheetsOpen, setSheetsOpen] = useState(false);
  const { data } = useCycleDataList();
  const { cycle_id } = useParams();
  const navigate = useNavigate();

  return (
    <Box>
      {data && (
        <Breadcrumbs sx={{ mb: 1.5, px: 0.5 }}>
          <Typography variant="body2" color="text.secondary">{data.farm_name}</Typography>
          <Typography variant="body2" color="text.secondary">{data.pond_name}</Typography>
          <Typography variant="body2" color="text.primary" fontWeight={600}>{data.cycle_name}</Typography>
        </Breadcrumbs>
      )}
      <Box sx={{ display: "flex", alignItems: "center", borderBottom: "1px solid #e0e0e0", mb: 1 }}>
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          sx={{ flexGrow: 1 }}
        >
          <Tab label="Data" />
          <Tab label="AI Insights" />
          <Tab label="Feeding" />
          <Tab label="Benchmark" />
        </Tabs>
        <Button
          size="small"
          variant="outlined"
          startIcon={<BarChartIcon />}
          onClick={() => navigate(`/dashboard/cycle/pl-report/${cycle_id}`)}
          sx={{ mr: 1, fontSize: 12 }}
        >
          P&amp;L Report
        </Button>
        <Tooltip title={sheetsOpen ? "Close Google Sheets" : "Connect Google Sheets"}>
          <IconButton
            size="small"
            sx={{ mr: 1.5 }}
            onClick={() => setSheetsOpen((v) => !v)}
            color={sheetsOpen ? "primary" : "default"}
          >
            <SiGooglesheets size={20} color={sheetsOpen ? "#474DA4" : "#34A853"} />
          </IconButton>
        </Tooltip>
      </Box>
      {tab === 0 && (
        <>
          <PopulateContent />
          <DataQuality />
        </>
      )}
      {tab === 1 && <AiInsights />}
      {tab === 2 && <FeedingRecommendation />}
      {tab === 3 && <BenchmarkSection />}
      {sheetsOpen && <GoogleSheets />}
    </Box>
  );
};

export default CycleDetail;
