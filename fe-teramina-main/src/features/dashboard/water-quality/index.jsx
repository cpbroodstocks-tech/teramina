import { Fragment } from "react";
import { useFilter } from "features/filter/water-quality/hooks";
import { useWaterQualityDashboard } from "widgets/water-quality/queries";
import Filter from "features/filter/water-quality/index2";
import { useTranslation } from "react-i18next";
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
import PageHeader from "components/page-header";

const WaterQuality = () => {
  const { t } = useTranslation();
  const { loading: filterLoading, filter, form, onFilterChange, submittedParams } = useFilter();
  const { data, isLoading: dataLoading, isError: error } = useWaterQualityDashboard(submittedParams);
  const loading = filterLoading || dataLoading;
  const [value, setValue] = useState(0);
  const linePlots = Array.isArray(data?.line_plot) ? data.line_plot : [];
  const scatterPlots = Array.isArray(data?.scatter_plot) ? data.scatter_plot : [];
  const tableRows = Array.isArray(data?.data) ? data.data : [];
  const tableColumns = Object.keys(tableRows[0] || {});

  const handleChange = (_event, newValue) => {
    setValue(newValue);
  };

  return (
    <Fragment>
      <div>
        <PageHeader title={t("WATER_QUALITY_ANALYSIS")} description={t("PAGE_DESCRIPTION.WATER_QUALITY")} />
        <Filter data={data} filter={filter} form={form} onFilterChange={onFilterChange} />
      </div>
      {loading && <Loader />}
      {error && <Error />}
      {!loading && !error && (!data || !Object.keys(data).length) && <Empty />}
      {!loading && !error && data && Object.keys(data).length > 0 && (
        <Box>
          <Box>
            <Tabs value={value} onChange={handleChange} variant="scrollable" scrollButtons="auto">
              <Tab label={t("LINE_CHART")} />
              <Tab label={t("SCATTER_CHART")} />
              <Tab label={t("TABLE")} />
            </Tabs>
          </Box>
          {value === 0 && (
            <Box>
              {linePlots.map((plot) => (
                <LineEcharts option={plot} key={plot.title} />
              ))}
            </Box>
          )}
          {value === 1 && (
            <Box>
              {scatterPlots.map((plot) => (
                <ScatterCharts option={plot} key={plot.title} />
              ))}
            </Box>
          )}
          {value === 2 && (
            <Box>
              <TableContainer component={Paper}>
                <Table aria-label={t("WATER_QUALITY_TABLE")}>
                  <TableHead>
                    <TableRow>
                      {tableColumns.map((key) => (
                        <TableCell align="center" key={key}>
                          {key.toUpperCase()}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {tableRows.map((row, index) => (
                      <TableRow
                        key={index}
                        sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
                      >
                        {Object.keys(row || {}).map((key) => (
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
