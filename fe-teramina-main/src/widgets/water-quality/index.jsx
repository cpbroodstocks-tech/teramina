import { Fragment } from "react";
import { useFilter } from "features/filter/water-quality/hooks";
import Filter from "features/filter/water-quality/index2";
import { useTranslation } from "react-i18next";
import { Typography } from "@mui/material";
import Loader from "components/loader";
import Error from "components/error";
import { useState } from "react";
import { Box, Tabs, Tab } from "@mui/material";
import LineEcharts from "components/echarts/line";
import ScatterCharts from "components/echarts/scatter";
import Empty from "components/empty";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Paper from "@mui/material/Paper";

const WaterQuality = () => {
  const { t } = useTranslation();
  const { loading, filter, data, error, formik, onFilterChange } = useFilter("/water_quality/get-water-quality-dashboard");
  const [value, setValue] = useState(0);

  const handleChange = (_event, newValue) => {
    setValue(newValue);
  };

  return (
    <Fragment>
      <div>
        <Typography variant="h1" sx={{ mb: "15px", fontSize: 40, textTransform: "capitalize", fontWeight: 700 }}>{t("WATER_QUALITY_ANALYSIS")}</Typography>
        <Filter data={data} filter={filter} formik={formik} onFilterChange={onFilterChange} />
      </div>
      {loading && <Loader />}
      {error && <Error />}
      {!loading && !error && !Object.keys(data).length && <Empty />}
      {!loading && !error && Object.keys(data).length > 0 && (
        <Box>
          <Box>
            <Tabs value={value} onChange={handleChange}>
              <Tab label="Line Chart" />
              <Tab label="Scatter Chart" />
              <Tab label="Table" />
            </Tabs>
          </Box>
          {value === 0 && (
            <Box>
              {data.line_plot.map((plot) => (
                <LineEcharts option={plot} key={plot.title} />
              ))}
            </Box>
          )}
          {value === 1 && (
            <Box>
              {data.scatter_plot.map((plot) => (
                <ScatterCharts option={plot} key={plot.title} />
              ))}
            </Box>
          )}
          {value === 2 && (
            <Box>
              <TableContainer component={Paper}>
                <Table aria-label="simple table">
                  <TableHead>
                    <TableRow>
                      {Object.keys(data.data[0]).map((key) => (
                        <TableCell align="center" key={key}>
                          {key.toUpperCase()}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.data.map((row, index) => (
                      <TableRow
                        key={index}
                        sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
                      >
                        {Object.keys(row).map((key) => (
                          <TableCell align="center" key={key}>
                            {row[key]}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </Box>
      )}
    </Fragment>
  );
};

export default WaterQuality;
