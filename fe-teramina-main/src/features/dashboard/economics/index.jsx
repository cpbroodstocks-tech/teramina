import { Fragment } from "react";
import { ReactSVG } from "react-svg";
import iconDoc from "/assets/images/icons/doc.svg";
import iconTotalCost from "/assets/images/icons/total-cost.svg";
import iconTotalRevenue from "/assets/images/icons/total-revenue.svg";
import iconTotalProfit from "/assets/images/icons/total-profit.svg";
import iconCostPerKilo from "/assets/images/icons/cost-per-kilo.svg";
import { useFilter } from "features/filter/default/hooks";
import { useEconomicsDashboard } from "widgets/economics/queries";
import Filter from "features/filter/summary";
import { useTranslation } from "react-i18next";
import { Card, CardContent, Typography, Avatar, Tooltip } from "@mui/material";
import { useStyles } from "widgets/economics/styles";
import { BsInfoSquare } from "react-icons/bs";
import classNames from "classnames";
import TableCostBreakdown from "widgets/economics/components/table-cost-breakdown";
import LineEcharts from "components/echarts/line";
import PieEcharts from "components/echarts/pie";
import Empty from "components/empty";
import Error from "components/error";
import Loader from "components/loader";
import { useLineEchartsGenerateOptions } from "hooks/useLineEchartsGenerateOptions";
import PageHeader from "components/page-header";

const Economics = () => {
  const { t } = useTranslation();
  const { loading: filterLoading, filter, form, onFilterChange, submittedParams } = useFilter();
  const { data, isLoading: dataLoading, isError: error } = useEconomicsDashboard(submittedParams);
  const loading = filterLoading || dataLoading;
  const { classes: styles } = useStyles();
  const { generateOptionsDefault } = useLineEchartsGenerateOptions();

  return (
    <Fragment>
      <PageHeader title={t("MENU.COST_ACCOUNTING")} description={t("PAGE_DESCRIPTION.ECONOMICS")} />
      <Filter filter={filter} form={form} onFilterChange={onFilterChange} />
      {loading && <Loader />}
      {error && <Error />}
      {!loading && !error && (!data || !Object.keys(data).length) && <Empty />}
      {!loading && !error && data && Object.keys(data).length > 0 && (
        Object(data).production_status.data.length > 3 ? (
          <Fragment>
            <section className={styles.sectionWrapper}>
              <Typography variant="h3">{data.profit_n_lost.title}</Typography>
              <div className={styles.economics}>
                {data.profit_n_lost.data.map((data, key) => (
                  <Card className={styles.economicsCard} key={key}>
                    <CardContent className={styles.economicsItems}>
                      <Avatar className={styles.economicsIcons} variant="rounded">
                        {data.title.toLowerCase() === "doc" && (
                          <ReactSVG src={iconDoc} />
                        )}
                        {data.title.toLowerCase() === "total cost" && (
                          <ReactSVG src={iconTotalCost} />
                        )}
                        {data.title.toLowerCase() === "total revenue" && (
                          <ReactSVG src={iconTotalRevenue} />
                        )}
                        {data.title.toLowerCase() === "total profit" && (
                          <ReactSVG src={iconTotalProfit} />
                        )}
                        {data.title.toLowerCase() === "cost per kilo" && (
                          <ReactSVG src={iconCostPerKilo} />
                        )}
                      </Avatar>
                      <div className={styles.economicsInfo}>
                        <Typography variant="body1">{data.title}</Typography>
                        <Typography variant="h4">{data.value}</Typography>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>

            <section className={styles.sectionWrapper}>
              <Typography variant="h3">{data.cost_breakdown.title}</Typography>
              <div className={styles.costBreakdown}>
                <Card className={styles.infoCard}>
                  <CardContent>
                    <TableCostBreakdown
                      data={data.cost_breakdown.table.data}
                      color={data.cost_breakdown.plot.color}
                    />
                  </CardContent>
                </Card>
                <Card className={styles.infoCard}>
                  <CardContent className={styles.echartsContainer}>
                    <PieEcharts showLegend option={data.cost_breakdown.plot} />
                  </CardContent>
                </Card>
              </div>
            </section>

            <section className={styles.sectionWrapper}>
              <Typography variant="h3">{data.production_status.title}</Typography>
              <div className={styles.productionStatus}>
                {data.production_status.data.map((data, key) => (
                  <Card
                    className={classNames(
                      styles.infoProductionStatus,
                      styles.cardToolTip
                    )}
                    key={key}
                  >
                    <CardContent className={styles.infoProductionStatusContent}>
                      <div className={styles.labelPerformance}>
                        <Typography variant="body1">{data.title}</Typography>
                        <Tooltip title={data.description} placement="top">
                          <div className={styles.tooltipInfo}>
                            <BsInfoSquare />
                          </div>
                        </Tooltip>
                      </div>
                      <div className={styles.dataPerformance}>
                        <Typography variant="h4">
                          {data.value}
                          <span> {data.unit}</span>
                        </Typography>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                <Card>
                  <CardContent className={styles.echartsContainer}>
                    <LineEcharts
                      option={generateOptionsDefault(
                        data.production_status.title,
                        data.production_status.plot
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
        ) : (
          <Fragment>
            <section className={styles.sectionWrapper}>
              <Typography variant="h3">{data.profit_n_lost.title}</Typography>
              <div className={styles.economics}>
                {data.profit_n_lost.data.map((data, key) => (
                  <Card className={styles.economicsCard} key={key}>
                    <CardContent className={styles.economicsItems}>
                      <Avatar className={styles.economicsIcons} variant="rounded">
                        {data.title.toLowerCase() === "doc" && (
                          <ReactSVG src={iconDoc} />
                        )}
                        {data.title.toLowerCase() === "total cost" && (
                          <ReactSVG src={iconTotalCost} />
                        )}
                        {data.title.toLowerCase() === "total revenue" && (
                          <ReactSVG src={iconTotalRevenue} />
                        )}
                        {data.title.toLowerCase() === "total profit" && (
                          <ReactSVG src={iconTotalProfit} />
                        )}
                        {data.title.toLowerCase() === "cost per kilo" && (
                          <ReactSVG src={iconCostPerKilo} />
                        )}
                      </Avatar>
                      <div className={styles.economicsInfo}>
                        <Typography variant="body1">{data.title}</Typography>
                        <Typography variant="h4">{data.value}</Typography>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>

            <section className={styles.sectionWrapper}>
              <Typography variant="h3">{data.cost_breakdown.title}</Typography>
              <div className={styles.costBreakdown}>
                <Card className={styles.infoCard}>
                  <CardContent>
                    <TableCostBreakdown
                      data={data.cost_breakdown.table.data}
                      color={data.cost_breakdown.plot.color}
                    />
                  </CardContent>
                </Card>
                <Card className={styles.infoCard}>
                  <CardContent className={styles.echartsContainer}>
                    <PieEcharts showLegend option={data.cost_breakdown.plot} />
                  </CardContent>
                </Card>
              </div>
            </section>

            <section className={styles.sectionWrapper}>
              <Typography variant="h3">{data.production_status.title}</Typography>
              <div className={styles.productionStatusSummary}>
                {data.production_status.data.map((data, key) => (
                  <Card
                    className={classNames(
                      styles.infoProductionStatus,
                      styles.cardToolTip
                    )}
                    key={key}
                  >
                    <CardContent className={styles.infoProductionStatusContent}>
                      <div className={styles.labelPerformance}>
                        <Typography variant="body1">{data.title}</Typography>
                        <Tooltip title={data.description} placement="top">
                          <div className={styles.tooltipInfo}>
                            <BsInfoSquare />
                          </div>
                        </Tooltip>
                      </div>
                      <div className={styles.dataPerformance}>
                        <Typography variant="h4">
                          {data.value}
                          <span> {data.unit}</span>
                        </Typography>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                <Card>
                  <CardContent className={styles.echartsContainer}>
                    <LineEcharts
                      option={generateOptionsDefault(
                        data.production_status.title,
                        data.production_status.plot
                      )}
                      inlineStyle={{
                        minHeight: "100%",
                      }}
                    />
                  </CardContent>
                </Card>
              </div>
            </section>
          </Fragment>
        )
      )}
    </Fragment>
  );
};

export default Economics;
