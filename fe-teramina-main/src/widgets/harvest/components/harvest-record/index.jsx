import { Fragment } from "react";
import { useStyles } from "widgets/harvest/components/harvest-record/styles";
import {
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import ModalAddHarvestRecord from "widgets/harvest/components/modal-add-harvest-record";
import ModalEditHarvestRecord from "widgets/harvest/components/modal-edit-harvest-record";
import { HARVEST_LENGTH } from "widgets/harvest/hooks";
import { useTranslation } from "react-i18next";

const HarvestRecord = ({ data, refetch, selectedFilter }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const columns = data.fields.map((column) => column.column);
  return (
    <Fragment>
      <div className={styles.sectionTitle}>
        <Typography variant="h3">{t("HARVEST_RECORD")}</Typography>
        {data.rows.length < HARVEST_LENGTH &&
          data.rows.filter((data) => data.harvest_type === "final").length ===
            0 && (
          <ModalAddHarvestRecord
            currentData={data}
            selectedFilter={selectedFilter}
            refetch={refetch}
          />
        )}
      </div>
      {data.rows.length > 0 ? (
        <div className={styles.harvestRecord}>
          <TableContainer component={Paper}>
            <Table className={styles.table}>
              <TableHead>
                <TableRow>
                  {data.fields.map((column, key) => (
                    <TableCell key={key}>{column.column_title}</TableCell>
                  ))}
                  <TableCell />
                </TableRow>
              </TableHead>
              <TableBody>
                {data.rows.map((value, key) => (
                  <TableRow key={key}>
                    {columns.map((column, key) => (
                      <TableCell key={key}>{value[column]}</TableCell>
                    ))}
                    <TableCell>
                      <ModalEditHarvestRecord
                        currentData={data}
                        selectedFilter={selectedFilter}
                        refetch={refetch}
                        harvestKey={
                          value.harvest_type !== "final"
                            ? `${value.harvest_type}${value.harvest_no}`
                            : value.harvest_type
                        }
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </div>
      ) : (
        <div className={styles.contentEmpty}>
          <div className={styles.lgEmpty}>
            <img src="/assets/images/empty-harvest.png" alt="empty" />
          </div>
        </div>
      )}
    </Fragment>
  );
};

export default HarvestRecord;
