import { Fragment, useState, useEffect } from "react";
import { Box } from "@mui/material";
import { ReactSVG } from "react-svg";
import { useFilter } from "features/filter/default/hooks";
import Filter from "features/filter/overview";
import { useTranslation } from "react-i18next";
import { Typography } from "@mui/material";
import {
  Card,
  CardContent,
  Avatar,
  Tooltip,
  Button,
} from "@mui/material";
import { FaDownload } from "react-icons/fa";
import { useStyles } from "widgets/overview/styles";
import iconTotalCost from "/assets/images/icons/total-cost.svg";
import iconTotalRevenue from "/assets/images/icons/total-revenue.svg";
import iconTotalProfit from "/assets/images/icons/total-profit.svg";
import iconCostPerKilo from "/assets/images/icons/cost-per-kilo.svg";
import { BsInfoSquare } from "react-icons/bs";
import {
  HiOutlineArrowNarrowUp,
  HiOutlineArrowNarrowDown,
} from "react-icons/hi";
import classNames from "classnames";
import LineEcharts from "components/echarts/line";
import ScatterCharts from "components/echarts/scatter";
import Error from "components/error";
import Loader from "components/loader";
import Empty from "components/empty";
import Stepper from "features/farm/stepper";
import DialogMessage from "components/dialog-message";
import { useUserCheckData } from "hooks/useUserCheckData";
import { useLineEchartsGenerateOptions } from "hooks/useLineEchartsGenerateOptions";
import { Markdown } from "components/markdown";
import { useToastStore } from "store/toast.store";
import { useCreateOverviewReport, useOverviewReportPoll } from "widgets/overview/queries";

const OverviewWidget = () => {
  const { t } = useTranslation();
  const { loading, filter, data, error, form, onFilterChange } = useFilter("/dashboard/overview");
  const { generateOptionsDefault, generateOptionsScatterOverview } = useLineEchartsGenerateOptions();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogTitle, setDialogTitle] = useState("");
  const [dialogMessage, setDialogMessage] = useState("");
  const [reportTaskId, setReportTaskId] = useState(null);

  const { classes: styles } = useStyles();
  const { setToast: toast } = useToastStore();

  const { mutate: createReport, isPending: creatingReport } = useCreateOverviewReport();
  const { data: pollResponse } = useOverviewReportPoll(reportTaskId);

  useEffect(() => {
    if (!pollResponse) return;
    if (pollResponse.type === "application/pdf") {
      const url = window.URL.createObjectURL(new Blob([pollResponse]));
      const link = document.createElement("a");
      const now = new Date();
      link.href = url;
      link.setAttribute("download", `report_teramina_${now.toISOString().slice(0, 19).replace(/[-T:]/g, "")}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setReportTaskId(null);
      setDialogOpen(false);
    } else {
      pollResponse.text().then((text) => {
        try {
          const json = JSON.parse(text);
          if (json.status === "FAILURE") {
            setReportTaskId(null);
            setDialogOpen(false);
            toast({ open: true, variant: "error", text: "Report generation failed. Please try again." });
          }
        } catch {
          // non-JSON response, keep polling
        }
      });
    }
  }, [pollResponse]);

  const button_loading = creatingReport || !!reportTaskId;

  const handleClick = () => {
    setDialogTitle("Info");
    setDialogMessage("Report download in progress. This may take up to 1 minute...");
    setDialogOpen(true);
    createReport({
      farm_id: localStorage.getItem("farm_id"),
      pond_id: localStorage.getItem("pond_id"),
      cycle_id: localStorage.getItem("cycle_id"),
      date: (localStorage.getItem("date") || "").replace(/"/g, ""),
      token: localStorage.getItem("authentication"),
    }, {
      onSuccess: (id) => setReportTaskId(id),
      onError: (err) => {
        setDialogOpen(false);
        toast({ open: true, variant: "error", text: err.message });
      },
    });
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
  };

  return (
    <Fragment>
      <Typography variant="h1" sx={{ mb: "15px", fontSize: 40, textTransform: "uppercase" }}>{t("MENU.OVERVIEW").toUpperCase()}</Typography>
      <Filter filter={filter} form={form} onFilterChange={onFilterChange} />
      {loading && <Loader />}
      {error && <Error />}
      {!loading && !error && !Object.keys(data || {}).length && <Empty />}
      {!loading && !error && Object.keys(data || {}).length > 0 && (
        <Fragment>
          {(() => {
            const performancePlot = data.performance.plot;
            let abwPlot = null;
            let sgrPlot = null;
            let biomassPlot = null;

            // Loop through the array once to find the plots
            for (const plot of performancePlot) {
              if (plot.title === "ABW Plot") {
                abwPlot = plot;
              } else if (plot.title === "SGR Plot") {
                sgrPlot = plot;
              } else if (plot.title === "Biomass Plot") {
                biomassPlot = plot;
              }
            }

            const plotsToRender = [abwPlot];
            if (sgrPlot) {
              plotsToRender.push(sgrPlot);
            } else if (biomassPlot) {
              plotsToRender.push(biomassPlot);
            }

            return (
              <Fragment>
                <section className={styles.sectionWrapper}>
                  <Typography variant="h3">{data.pond_info.title}</Typography>
                  <div className={styles.pondInfo}>
                    {data.pond_info.data.map((info, key) => (
                      <Card className={styles.infoCard} key={key}>
                        <CardContent className={styles.wrapPodInfo}>
                          <div className={styles.pondInfoTitle}>
                            <Typography variant="body1">{info.title}</Typography>
                          </div>
                          <Typography variant="h4">
                            {info.value}
                            <span> {info.unit}</span>
                          </Typography>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </section>
                <section className={styles.sectionWrapperSummary}>
                  <Markdown data={data} />
                </section>
                <section className={styles.sectionWrapper}>
                  <Typography variant="h3">{data.performance.title}</Typography>
                  <div >
                    {
                      data.performance?.data?.length > 4 ? (
                        <div>
                          <div className={styles.performanceMetric} >
                            {data.performance.data
                              .map((data, key) => (
                                <Card
                                  className={classNames(
                                    styles.infoPerformance,
                                    styles.cardToolTip
                                  )}
                                  key={key}
                                >
                                  <CardContent className={styles.infoPerformanceContent}>
                                    <div className={styles.labelPerformance}>
                                      <Typography variant="body1">{data.title}</Typography>
                                      <Tooltip title={data.description} placement="top">
                                        <div className={styles.tooltipInfo}>
                                          <BsInfoSquare />
                                        </div>
                                      </Tooltip>
                                    </div>
                                    <div>
                                      <Typography variant="h4">
                                        {data.value}
                                        <span> {data.unit}</span>
                                      </Typography>
                                      <Typography
                                        variant="h5"
                                        className={
                                          data.current_status === "increase"
                                            ? styles.persentaseUp
                                            : styles.persentaseDown
                                        }
                                      >
                                        {data.change_ratio}%
                                        {data.current_status === "increase" && (
                                          <HiOutlineArrowNarrowUp />
                                        )}
                                        {data.current_status !== "increase" && (
                                          <HiOutlineArrowNarrowDown />
                                        )}
                                      </Typography>
                                    </div>
                                  </CardContent>
                                </Card>
                              ))
                            }
                          </div>
                          <div className={styles.performancPlot}>
                            {plotsToRender.map((plot, key) => (
                              <Card
                                className={classNames(
                                  styles.infoPerformance
                                )}
                                key={key}
                              >
                                <CardContent className={styles.echartsContainer}>
                                  {plot.title === "SGR Plot" || plot.title === "Biomass Plot" || plot.title === null? (
                                    <LineEcharts
                                      option={generateOptionsDefault(
                                        plot.title,
                                        plot.echart_option
                                      )}
                                      inlineStyle={{
                                        minHeight: "100%",
                                        height: "250px",
                                      }}
                                    />
                                  ) : (
                                    <ScatterCharts
                                      option={generateOptionsScatterOverview(
                                        plot.title,
                                        plot.echart_option
                                      )}
                                      inlineStyle={{
                                        minHeight: "100%",
                                        height: "250px",
                                      }}
                                    />
                                  )
                                  }
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div>
                          <div className={styles.performanceMetricAggregate} >
                            {data.performance.data
                              .map((data, key) => (
                                <Card
                                  className={classNames(
                                    styles.infoPerformance,
                                    styles.cardToolTip
                                  )}
                                  key={key}
                                >
                                  <CardContent className={styles.infoPerformanceContent}>
                                    <div className={styles.labelPerformance}>
                                      <Typography variant="body1">{data.title}</Typography>
                                      <Tooltip title={data.description} placement="top">
                                        <div className={styles.tooltipInfo}>
                                          <BsInfoSquare />
                                        </div>
                                      </Tooltip>
                                    </div>
                                    <div>
                                      <Typography variant="h4">
                                        {data.value}
                                        <span> {data.unit}</span>
                                      </Typography>
                                      <Typography
                                        variant="h5"
                                        className={
                                          data.current_status === "increase"
                                            ? styles.persentaseUp
                                            : styles.persentaseDown
                                        }
                                      >
                                        {data.change_ratio}%
                                        {data.current_status === "increase" && (
                                          <HiOutlineArrowNarrowUp />
                                        )}
                                        {data.current_status !== "increase" && (
                                          <HiOutlineArrowNarrowDown />
                                        )}
                                      </Typography>
                                    </div>
                                  </CardContent>
                                </Card>
                              ))}
                          </div>
                          <div>
                            {data.performance.plot.map((plot, key) => (
                              <Card
                                className={classNames(
                                  styles.infoPerformance
                                )}
                                key={key}
                              >
                                <CardContent className={styles.echartsContainer}>
                                  <LineEcharts
                                    option={generateOptionsDefault(
                                      plot.title,
                                      plot.echart_option
                                    )}
                                    inlineStyle={{
                                      minHeight: "100%",
                                      height: "250px",
                                    }}
                                  />
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        </div>
                      )
                    }
                  </div>
                </section>
                <section className={styles.sectionWrapper}>
                  <Typography variant="h3">Economics</Typography>
                  <div className={styles.economics}>
                    {data.economics.data.map((data, key) => (
                      <Card className={styles.economicsCard} key={key}>
                        <CardContent className={styles.economicsItems}>
                          <Avatar className={styles.economicsIcons} variant="rounded">
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
                  <Card
                    className={`${styles.infoPerformance} ${styles.infoPerformanceE}`}
                  >
                    <CardContent className={styles.reportECardContainer}>
                      <div className={styles.infoPerformanceEContentItemDescription}>
                        <Typography variant="body2">
                          If you would like to obtain a comprehensive report detailing the current farm condition encompassing farming data,
                          finance, and water quality, simply click the &apos;Report&apos; button.
                        </Typography>
                      </div>
                      <div className={styles.infoPerformanceEContentItemButton}>
                        <Button onClick={handleClick} variant="contained" startIcon={<FaDownload />} disabled={button_loading}>
                          Report
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </section>
                <DialogMessage
                  open={dialogOpen}
                  onClose={handleCloseDialog}
                  title={dialogTitle}
                  message={dialogMessage}
                  loading={button_loading}
                />
              </Fragment>
            );
          })()}
        </Fragment>
      )}
    </Fragment>
  );
};

const Overview = () => {
  const { loading, data, error } = useUserCheckData();

  if (loading) return <Loader />;
  if (error) return <Error />;
  if (!data) return (
    <Box sx={{ position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh", bgcolor: "background.default", zIndex: 1200, overflowY: "auto", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <Stepper />
    </Box>
  );
  return <OverviewWidget />;
};

export default Overview;
