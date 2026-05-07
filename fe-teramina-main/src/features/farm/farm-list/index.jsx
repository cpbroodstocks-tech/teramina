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
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import EastIcon from "@mui/icons-material/East";
import ModalFarmAdd from "features/farm/modal-add-farm";
import ModalFarmEdit from "features/farm/modal-edit-farm";
import ModalFarmDelete from "features/farm/modal-delete-farm";
import { useStyles } from "features/farm/farm-list/styles";
import Search from "components/search";
import { useDebounce } from "hooks/useDebounce";
import { useTranslation } from "react-i18next";

const FarmList = ({ data }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { classes: styles } = useStyles();
  const [search, setSearch] = useState("");

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
            {table.map((farm, key) => (
              <TableRow key={key}>
                <TableCell>{farm.name}</TableCell>
                <TableCell>{farm.location}</TableCell>
                <TableCell>{farm.active_pond} Pond</TableCell>
                <TableCell>{farm.inactive_pond} Pond</TableCell>
                <TableCell>{farm.total_pond} Pond</TableCell>
                <TableCell>
                  <div className={styles.actionContainer}>
                    <ModalFarmEdit data={farm} />
                    <ModalFarmDelete data={farm} />
                    <Button
                      className={styles.btnViewMore}
                      onClick={() => navigate(`/dashboard/pond/${farm._id}`)}
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

export default FarmList;
