import { Fragment, useMemo, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Box,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import EastIcon from "@mui/icons-material/East";
import BarChartIcon from "@mui/icons-material/BarChart";
import ModalFarmAdd from "features/farm/modal-add-farm";
import ModalFarmEdit from "features/farm/modal-edit-farm";
import ModalFarmDelete from "features/farm/modal-delete-farm";
import { useStyles } from "features/farm/farm-list/styles";
import Search from "components/search";
import { useDebounce } from "hooks/useDebounce";
import { useTranslation } from "react-i18next";
import { useDashboardContextStore } from "store/dashboard-context.store";
import ResponsiveDataList from "components/responsive-data-list";

const FarmList = ({ data }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { classes: styles } = useStyles();
  const [search, setSearch] = useState("");
  const setContext = useDashboardContextStore((state) => state.setContext);

  const handleSearchChange = useDebounce(
    (event) => setSearch(event.target.value),
    1000
  );

  const table = useMemo(() => {
    if (!search) return data;
    return data.filter(
      (farm) =>
        farm.name.toLowerCase().includes(search.toLowerCase()) ||
        farm.location.toLowerCase().includes(search.toLowerCase())
    );
  }, [search]);

  const renderActions = (farm) => (
    <>
      <ModalFarmEdit data={farm} />
      <ModalFarmDelete data={farm} />
      <Button
        size="small"
        variant="outlined"
        startIcon={<BarChartIcon fontSize="small" />}
        onClick={() => navigate(`/dashboard/farm/pl-report/${farm._id}`)}
        sx={{ fontSize: 12 }}
      >
        P&amp;L
      </Button>
      <Button
        className={styles.btnViewMore}
        onClick={() => {
          setContext({ farm_id: farm._id, farm_name: farm.name, pond_id: "", pond_name: "", cycle_id: "", cycle_name: "" });
          navigate(`/dashboard/pond/${farm._id}`);
        }}
      >
        <Typography variant="span" className={styles.btnViewMoreText}>
          {t("VIEW_MORE")}
        </Typography>
        <EastIcon className={styles.btnViewMoreIcon} />
      </Button>
    </>
  );

  return (
    <Fragment>
      <Typography variant="h2" className={styles.pageTitle}>
        {t("DATA_MANAGEMENT")}
      </Typography>
      <Typography variant="h3" className={styles.sectionTitle}>
        {t("FARM_LIST")}
      </Typography>
      {/* Pop Up Add Farm */}
      <div className={styles.toolbarTable}>
        <ModalFarmAdd />
        <Search onChange={handleSearchChange} />
      </div>

      {/* List Farm */}
      <ResponsiveDataList
        items={table}
        getKey={(farm) => farm._id}
        fields={[
          { label: t("FARM_NAME"), value: (farm) => farm.name },
          { label: t("FARM_LOCATION"), value: (farm) => farm.location },
          { label: t("ACTIVE_POND"), value: (farm) => farm.active_pond },
          { label: t("INACTIVE_POND"), value: (farm) => farm.inactive_pond },
          { label: t("TOTAL_POND"), value: (farm) => farm.total_pond },
        ]}
        renderActions={renderActions}
      />
      <Box sx={{ display: { xs: "none", md: "block" } }}>
        <TableContainer component={Paper}>
          <Table className={styles.table}>
            <TableHead>
              <TableRow>
                <TableCell>{t("FARM_NAME")}</TableCell>
                <TableCell>{t("FARM_LOCATION")}</TableCell>
                <TableCell>{t("ACTIVE_POND")}</TableCell>
                <TableCell>{t("INACTIVE_POND")}</TableCell>
                <TableCell>{t("TOTAL_POND")}</TableCell>
                <TableCell>&nbsp;</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {table.map((farm) => (
                <TableRow key={farm._id}>
                  <TableCell>{farm.name}</TableCell>
                  <TableCell>{farm.location}</TableCell>
                  <TableCell>{farm.active_pond} Pond</TableCell>
                  <TableCell>{farm.inactive_pond} Pond</TableCell>
                  <TableCell>{farm.total_pond} Pond</TableCell>
                  <TableCell><div className={styles.actionContainer}>{renderActions(farm)}</div></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Fragment>
  );
};

export default FarmList;
