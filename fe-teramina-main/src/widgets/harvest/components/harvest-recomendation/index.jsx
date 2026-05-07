import { Fragment } from "react";
import {
  TableContainer,
  Paper,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Typography,
} from "@mui/material";
import { useStyles } from "widgets/harvest/components/harvest-recomendation/styles";
import { useTranslation } from "react-i18next";

const HarvestRecomendationTable = ({ data }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();

  const columns = data.fields.map((column) => column.column);
  return (
    <Fragment>
      <Typography variant="h3">{t("HARVER_RECOMMENDATION")}</Typography>
      <div className={styles.harvestInfo}>
        <TableContainer component={Paper}>
          <Table className={styles.table}>
            <TableHead>
              <TableRow>
                {data.fields.map((column, key) => (
                  <TableCell key={key}>{column.column_title}</TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {data.rows.map((data, key) => (
                <TableRow key={key}>
                  {columns.map((column, key) => (
                    <TableCell key={key}>{data[column]}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </div>
    </Fragment>
  );
};

export default HarvestRecomendationTable;
