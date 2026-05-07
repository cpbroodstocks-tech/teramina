import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import { Fragment } from "react";
import { useStyles } from "widgets/harvest/components/table-harvest-simulation/styles";

const TableHarvestSimulation = ({ data }) => {
  const { classes: styles } = useStyles();
  const columns = data.fields.map((column) => column.column);
  return (
    <Fragment>
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
            {data.rows.map((value, key) => (
              <TableRow key={key}>
                {columns.map((column, key) => (
                  <TableCell key={key}>{value[column]}</TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Fragment>
  );
};

export default TableHarvestSimulation;
