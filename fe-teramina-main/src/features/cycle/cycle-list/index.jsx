import { Fragment, useState, useMemo } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Typography,
} from "@mui/material";
import EastIcon from "@mui/icons-material/East";
import { BiChevronLeftCircle } from "react-icons/bi";
import { useNavigate } from "react-router-dom";
import ModalCycleAdd from "features/cycle/modal-add-cycle";
import ModalCycleEdit from "features/cycle/modal-edit-cycle";
import ModalCycleDelete from "features/cycle/modal-delete-cycle";
import { useStyles } from "features/cycle/cycle-list/styles";
import Search from "components/search";
import { useDebounce } from "hooks/useDebounce";
import { useTranslation } from "react-i18next";
import PondMemoryPanel from "components/pond-memory-panel";
import { useDashboardContextStore } from "store/dashboard-context.store";

const PondList = ({ data }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { classes: styles } = useStyles();
  const [search, setSearch] = useState("");
  const farmId = data.farm_id || localStorage.getItem("farm_id") || "";
  const pondId = data.pond_id || localStorage.getItem("pond_id") || "";
  const setContext = useDashboardContextStore((state) => state.setContext);

  const handleSearchChange = useDebounce(
    (event) => setSearch(event.target.value),
    1000
  );

  const table = useMemo(() => {
    if (!search) return data.data;
    return data.data.filter((pond) =>
      pond.name.toLowerCase().includes(search.toLowerCase())
    );
  }, [search]);

  return (
    <Fragment>
      <Typography variant="h2" className={styles.pageTitle}>
        {t("DATA_MANAGEMENT")}
      </Typography>
      <Typography variant="h3" className={styles.sectionTitle}>
        {t("CYCLE_LIST_IN_POND", { name: data.pond_name })}
      </Typography>
      <Button className={styles.btnBack} onClick={() => navigate(-1)}>
        <BiChevronLeftCircle className={styles.btnBackIcon} />
        <Typography variant="span" className={styles.btnBackText}>
          {t("BACK_TO_POND_LIST")}
        </Typography>
      </Button>
      {/* Pop Up Add Farm */}
      <div className={styles.toolbarTable}>
        <ModalCycleAdd data={data} />
        <Search onChange={handleSearchChange} />
      </div>
      <PondMemoryPanel farmId={farmId} pondId={pondId} pondName={data.pond_name} />
      {/* List Farm */}
      <TableContainer component={Paper}>
        <Table className={styles.table}>
          <TableHead>
            <TableRow>
              <TableCell>{t("CYCLE_NAME")}</TableCell>
              <TableCell>{t("START_DATE")}</TableCell>
              <TableCell>&nbsp;</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {table.map((cycle, key) => (
              <TableRow key={key}>
                <TableCell>{cycle.name}</TableCell>
                <TableCell>{cycle.start_date}</TableCell>
                <TableCell>
                  <div className={styles.actionContainer}>
                    <ModalCycleEdit data={cycle} />
                    <ModalCycleDelete data={cycle} />
                    <Button
                      className={styles.btnViewMore}
                      onClick={() => {
                        localStorage.setItem("selectedCycleStartDate", cycle.start_date);
                        setContext({ cycle_id: cycle._id, cycle_name: cycle.name });
                        navigate(`/dashboard/cycle/detail/${cycle._id}`);
                      }}
                    >
                      <Typography
                        variant="span"
                        className={styles.btnViewMoreText}
                      >
                        {t("VIEW_MORE")}
                      </Typography>
                      <EastIcon className={styles.btnViewMoreIcon} />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Fragment>
  );
};

export default PondList;
