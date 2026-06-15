import { Fragment } from "react";
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
import { BiChevronLeftCircle } from "react-icons/bi";
import { useNavigate } from "react-router-dom";
import ModalPopulateAdd from "features/cycle-detail/modal-add-populate";
import ButtonDownloadData from "features/cycle-detail/download-data";
import { useStyles } from "features/cycle-detail/populate-list/styles";
import { useTranslation } from "react-i18next";
import ResponsiveDataList from "components/responsive-data-list";

const PopulateList = ({ data }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { classes: styles } = useStyles();

  return (
    <Fragment>
      <Typography variant="h2" className={styles.pageTitle}>
        {t("DATA_MANAGEMENT")}
      </Typography>
      <Typography variant="h3" className={styles.sectionTitle}>
        {t("CYCLE_POPULATION_LIST_IN_FARM", { name: data.farm_name })}
        <br />
        {t("POND_NAME_VALUE", { name: data.pond_name })},{" "}
        {t("CYCLE_NAME_VALUE", { name: data.cycle_name })}
      </Typography>
      <Button className={styles.btnBack} onClick={() => navigate(-1)}>
        <BiChevronLeftCircle className={styles.btnBackIcon} />
        <Typography variant="span" className={styles.btnBackText}>
          {t("BACK_TO_CYCLE_LIST")}
        </Typography>
      </Button>
      {/* Pop Up Add Farm */}
      <div className={styles.toolbarTable}>
        <ModalPopulateAdd data={data} />
        <ButtonDownloadData />
      </div>
      {/* List Farm */}
      <ResponsiveDataList
        items={data.data}
        getKey={(_, index) => index}
        fields={data.columns.map((column) => ({ label: column, value: (population) => population[column] }))}
      />
      <Box sx={{ display: { xs: "none", md: "block" } }}>
        <TableContainer component={Paper}>
          <Table className={styles.table}>
            <TableHead>
              <TableRow>
                {data.columns.map((column) => <TableCell key={column}>{column}</TableCell>)}
              </TableRow>
            </TableHead>
            <TableBody>
              {data.data.map((populations, key) => (
                <TableRow key={key}>
                  {data.columns.map((column) => <TableCell key={column}>{populations[column]}</TableCell>)}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Fragment>
  );
};

export default PopulateList;
