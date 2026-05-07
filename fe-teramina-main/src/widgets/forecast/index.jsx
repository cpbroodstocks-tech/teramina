import { Fragment } from "react";
import { useFilter } from "features/filter/forecast/hooks";
import Filter from "features/filter/default";
import { useTranslation } from "react-i18next";
import classNames from "classnames";
import {
  Card,
  CardContent,
  Chip,
  Typography,
  IconButton,
  Tooltip,
} from "@mui/material";
import { BsInfoSquare } from "react-icons/bs";
import { useStyles } from "widgets/forecast/styles";
import LineEcharts from "components/echarts/line";
import Loader from "components/loader";
import Error from "components/error";
import Empty from "components/empty";
import { useLineEchartsGenerateOptions } from "hooks/useLineEchartsGenerateOptions";
import { useConfidenceBands, useProphetForecast } from "widgets/forecast/queries";

const Forecast = () => {
  const { t } = useTranslation();
  const { loading, filter, data, error, formik, onFilterChange } = useFilter("/dashboard/forecast");
  const { classes: styles } = useStyles();
  const { generateOptionsDefault, generateOptionsWithMoneyFormatYAxis } =
    useLineEchartsGenerateOptions();

  const cycleId = filter?.cycle_id || null;
  const { data: bands, isLoading: bandsLoading } = useConfidenceBands(cycleId);
  const { data: prophetBands } = useProphetForecast(cycleId);

  const bandsOption = bands && bands.docs && bands.docs.length > 0
    ? {
      title: { text: "ABW Growth Confidence Bands (80%)", textStyle: { fontSize: 14 } },
      tooltip: { trigger: "axis" },
      legend: { data: ["Lower 80%", "Upper 80%"] },
      xAxis: { type: "category", data: bands.docs, name: "DOC" },
      yAxis: { type: "value", name: "ABW (g)" },
      series: [
        {
          name: "Lower 80%",
          type: "line",
          data: bands.abw_lower_80,
          areaStyle: { opacity: 0.15 },
          lineStyle: { opacity: 0.5 },
          itemStyle: { color: "#474DA4" },
        },
        {
          name: "Upper 80%",
          type: "line",
          data: bands.abw_upper_80,
          areaStyle: { opacity: 0.15 },
          lineStyle: { opacity: 0.5 },
          itemStyle: { color: "#FBBC05" },
        },
      ],
    }
    : null;

  return (
    <Fragment>
      <Typography variant="h1" sx={{ mb: "15px", fontSize: 40, textTransform: "uppercase" }}>{t("MENU.FORECAST")}</Typography>
      <Filter data={data} filter={filter} formik={formik} onFilterChange={onFilterChange} />
      {loading && <Loader />}
      {error && <Error />}
      {!loading && !error && !Object.keys(data).length && <Empty />}
      {!loading && !error && Object.keys(data).length > 0 && (
        <Fragment>
          <section className={styles.sectionContainer}>
            <Typography variant="h2" className={styles.sectionTitle}>
              Feeding Forecast
            </Typography>
            <div className={styles.productionFeedingForecast}>
              {data.feeding_forecast.data
                .filter((data) => data.title !== "Forcasted FCR")
                .map((data, key) => (
                  <Card
                    className={classNames(
                      styles.card,
                      key === 0 && styles.productionFeedingForecastA,
                      key === 1 && styles.productionFeedingForecastB,
                      key === 2 && styles.productionFeedingForecastC,
                      key === 3 && styles.productionFeedingForecastD,
                      styles.cardToolTip
                    )}
                    key={key}
                  >
                    <CardContent>
                      <div className={styles.cardTitleContainer}>
                        <div className={styles.cardTitleLabelContainer}>
                          {data.title !== "DOC" && (
                            <div
                              className={styles.cardTitleLabelColor}
                              style={{
                                backgroundColor:
                                  key % 2 === 0 ? "#474DA4" : "#FBBC05",
                              }}
                            />
                          )}
                          <Typography variant="h3" className={styles.cardTitle}>
                            {data.title}
                          </Typography>
                        </div>
                        {data.title !== "DOC" && (
                          <Tooltip title={data.description} arrow placement="top">
                            <IconButton
                              aria-label="info"
                              className={styles.infoIconContainer}
                            >
                              <BsInfoSquare className={styles.infoIcon} />
                            </IconButton>
                          </Tooltip>
                        )}
                      </div>
                      <Typography variant="h4" className={styles.cardValue}>
                        {data.value} <span>{data.unit}</span>
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
            </div>
          </section>
          <section className={styles.sectionContainer}>
            <Typography variant="h2" className={styles.sectionTitle}>
              Production Forecast
            </Typography>
            <div className={styles.productionEconomicForecast}>
              {data.production_forecast.data
                .filter(
                  (data) => data.title !== "DOC" && data.title !== "Forcasted FCR"
                )
                .map((data, key) => (
                  <Card
                    className={classNames(
                      styles.card,
                      key === 0 && styles.productionEconomicForecastA,
                      key === 1 && styles.productionEconomicForecastB,
                      key === 2 && styles.productionEconomicForecastC,
                      key === 3 && styles.productionEconomicForecastD,
                      styles.cardToolTip
                    )}
                    key={key}
                  >
                    <CardContent>
                      <div className={styles.cardTitleContainer}>
                        <div className={styles.cardTitleLabelContainer}>
                          <div
                            className={styles.cardTitleLabelColor}
                            style={{
                              backgroundColor:
                                key % 2 === 0 ? "#474DA4" : "#FBBC05",
                            }}
                          />
                          <Typography variant="h3" className={styles.cardTitle}>
                            {data.title}
                          </Typography>
                        </div>
                        <Tooltip title={data.description} arrow placement="top">
                          <IconButton
                            aria-label="info"
                            className={styles.infoIconContainer}
                          >
                            <BsInfoSquare className={styles.infoIcon} />
                          </IconButton>
                        </Tooltip>
                      </div>
                      <Typography variant="h4" className={styles.cardValue}>
                        {data.value} <span>{data.unit}</span>
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              <Card
                className={classNames(
                  styles.card,
                  styles.productionEconomicForecastE
                )}
              >
                <CardContent className={styles.echartsContainer}>
                  <LineEcharts
                    option={generateOptionsDefault(
                      data.production_forecast.plot.forecast_biomass.title.text,
                      data.production_forecast.plot.forecast_biomass
                    )}
                    inlineStyle={{
                      minHeight: "100%",
                      height: "250px",
                    }}
                  />
                </CardContent>
              </Card>
              <Card
                className={classNames(
                  styles.card,
                  styles.productionEconomicForecastF
                )}
              >
                <CardContent className={styles.echartsContainer}>
                  <LineEcharts
                    option={generateOptionsDefault(
                      data.production_forecast.plot.forecast_abw.title.text,
                      data.production_forecast.plot.forecast_abw
                    )}
                    inlineStyle={{
                      minHeight: "100%",
                      height: "250px",
                    }}
                  />
                </CardContent>
              </Card>
            </div>
          </section>
          {!bandsLoading && bandsOption && (
            <section className={styles.sectionContainer}>
              <Typography variant="h2" className={styles.sectionTitle}>
                ABW Confidence Bands — Bootstrap 80%
              </Typography>
              <Card className={styles.card}>
                <CardContent className={styles.echartsContainer}>
                  <LineEcharts
                    option={bandsOption}
                    inlineStyle={{ minHeight: "100%", height: "280px" }}
                  />
                </CardContent>
              </Card>
            </section>
          )}
          {prophetBands && prophetBands.docs && prophetBands.docs.length > 0 && (
            <section className={styles.sectionContainer}>
              <Typography variant="h2" className={styles.sectionTitle}>
                ABW Forecast — Prophet 80% Confidence
                <Chip
                  label={`R² ${prophetBands.model_info?.r_squared?.toFixed(2) ?? "—"}`}
                  size="small"
                  style={{ marginLeft: 8, fontSize: 11 }}
                />
              </Typography>
              <Card className={styles.card}>
                <CardContent className={styles.echartsContainer}>
                  <LineEcharts
                    option={{
                      title: { text: "Medium-Horizon ABW Forecast (Prophet)", textStyle: { fontSize: 14 } },
                      tooltip: { trigger: "axis" },
                      legend: { data: ["Forecast", "Lower 80%", "Upper 80%"] },
                      xAxis: { type: "category", data: prophetBands.docs, name: "DOC" },
                      yAxis: { type: "value", name: "ABW (g)" },
                      series: [
                        {
                          name: "Forecast",
                          type: "line",
                          data: prophetBands.abw_forecast,
                          lineStyle: { width: 2 },
                          itemStyle: { color: "#474DA4" },
                          symbol: "none",
                        },
                        {
                          name: "Lower 80%",
                          type: "line",
                          data: prophetBands.abw_lower_80,
                          areaStyle: { opacity: 0.12, color: "#474DA4" },
                          lineStyle: { opacity: 0.4, width: 1 },
                          itemStyle: { color: "#474DA4" },
                          symbol: "none",
                          stack: "confidence",
                        },
                        {
                          name: "Upper 80%",
                          type: "line",
                          data: prophetBands.abw_upper_80,
                          areaStyle: { opacity: 0.12, color: "#474DA4" },
                          lineStyle: { opacity: 0.4, width: 1 },
                          itemStyle: { color: "#474DA4" },
                          symbol: "none",
                        },
                      ],
                    }}
                    inlineStyle={{ minHeight: "100%", height: "280px" }}
                  />
                </CardContent>
              </Card>
            </section>
          )}
          <section className={styles.sectionContainer}>
            <Typography variant="h2" className={styles.sectionTitle}>
              {data.economic_forecast.title}
            </Typography>
            <div className={styles.productionEconomicForecast}>
              {data.economic_forecast.data.map((data, key) => (
                <Card
                  className={classNames(
                    styles.card,
                    key === 0 && styles.productionEconomicForecastA,
                    key === 1 && styles.productionEconomicForecastB,
                    key === 2 && styles.productionEconomicForecastC,
                    key === 3 && styles.productionEconomicForecastD,
                    styles.cardToolTip
                  )}
                  key={key}
                >
                  <CardContent>
                    <div className={styles.cardTitleContainer}>
                      <div className={styles.cardTitleLabelContainer}>
                        <div
                          className={styles.cardTitleLabelColor}
                          style={{
                            backgroundColor: key % 2 === 0 ? "#474DA4" : "#FBBC05",
                          }}
                        />
                        <Typography variant="h3" className={styles.cardTitle}>
                          {data.title}
                        </Typography>
                      </div>
                      <Tooltip title={data.description} arrow placement="top">
                        <IconButton
                          aria-label="info"
                          className={styles.infoIconContainer}
                        >
                          <BsInfoSquare className={styles.infoIcon} />
                        </IconButton>
                      </Tooltip>
                    </div>
                    <Typography variant="h4" className={styles.cardValue}>
                      {data.value}
                    </Typography>
                  </CardContent>
                </Card>
              ))}

              <Card
                className={classNames(
                  styles.card,
                  styles.productionEconomicForecastE
                )}
              >
                <CardContent className={styles.echartsContainer}>
                  <LineEcharts
                    option={generateOptionsWithMoneyFormatYAxis(
                      data.economic_forecast.plot.forecast_revenue.title.text,
                      data.economic_forecast.plot.forecast_revenue
                    )}
                    inlineStyle={{
                      minHeight: "100%",
                      height: "250px",
                    }}
                  />
                </CardContent>
              </Card>
              <Card
                className={classNames(
                  styles.card,
                  styles.productionEconomicForecastF
                )}
              >
                <CardContent className={styles.echartsContainer}>
                  <LineEcharts
                    option={generateOptionsWithMoneyFormatYAxis(
                      data.economic_forecast.plot.forecast_profit.title.text,
                      data.economic_forecast.plot.forecast_profit
                    )}
                    inlineStyle={{
                      minHeight: "100%",
                      height: "250px",
                    }}
                  />
                </CardContent>
              </Card>
            </div>
          </section>
        </Fragment>
      )}
    </Fragment>
  );
};

export default Forecast;
