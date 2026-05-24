import { Fragment } from "react";
import { useFilter } from "features/filter/feeding/hooks";
import { useFeedingDashboard } from "widgets/feeding/queries";
import Filter from "features/filter/default";
import { useTranslation } from "react-i18next";
import {
  Card,
  CardContent,
  Typography,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import { BsInfoSquare } from "react-icons/bs";
import { useStyles } from "widgets/feeding/styles";
import classNames from "classnames";
import LineEcharts from "components/echarts/line";
import Error from "components/error";
import Loader from "components/loader";
import Empty from "components/empty";
import ModalAddFeeding from "features/feeding/modal-add-feeding";
import { useLineEchartsGenerateOptions } from "hooks/useLineEchartsGenerateOptions";

const Feeding = () => {
  const { t } = useTranslation();
  const { loading: filterLoading, filter, form, selectedFilter, onFilterChange, submittedParams } = useFilter();
  const { data, isLoading: dataLoading, isError: error, refetch } = useFeedingDashboard(submittedParams);
  const loading = filterLoading || dataLoading;
  const { classes: styles } = useStyles();
  const { generateOptionsDefault } = useLineEchartsGenerateOptions();

  return (
    <Fragment>
      <Typography variant="h1" sx={{ mb: "15px", fontSize: 40, textTransform: "uppercase" }}>{t("MENU.FEEDING")}</Typography>
      <Filter data={data} filter={filter} form={form} onFilterChange={onFilterChange} />
      {loading && <Loader />}
      {error && <Error />}
      {!loading && !error && (!data || !Object.keys(data).length) && <Empty />}
      {!loading && !error && data && Object.keys(data).length > 0 && (
        <Fragment>
          <section className={styles.sectionContainer}>
            <Typography variant="h2" className={styles.sectionTitle}>
              {data.feed_status.title}
            </Typography>
            <div className={styles.status}>
              {data.feed_status &&
                data.feed_status.data.length > 0 &&
                data.feed_status.data.map((status, key) => (
                  <Card className={styles.card} key={key}>
                    <CardContent className={styles.cardContent}>
                      <div className={styles.cardTitleContainer}>
                        <Typography variant="h3" className={styles.cardTitle}>
                          {status.title}
                        </Typography>
                      </div>
                      <Typography variant="h4" className={styles.cardValue}>
                        {status.value} <span>{status.unit}</span>
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
            </div>
          </section>
          <section className={styles.sectionContainer}>
            <Typography variant="h2" className={styles.sectionTitle}>
              {data.feed_adjustment.title}
            </Typography>
            <div className={styles.adjustment}>
              <div className={styles.column}>
                {data.feed_adjustment &&
                  data.feed_adjustment.data.length > 0 &&
                  data.feed_adjustment.data
                    .filter(
                      (filtered) =>
                        filtered.title === "Original Feeding Rate" ||
                        filtered.title === "Adjustment Feeding Rate"
                    )
                    .map((adjustment, key) => (
                      <Card
                        className={classNames(styles.card, styles.cardToolTip)}
                        key={key}
                      >
                        <CardContent className={styles.cardContent}>
                          <div className={styles.cardTitleContainer}>
                            <Typography variant="h3" className={styles.cardTitle}>
                              {adjustment.title}
                            </Typography>
                            <Tooltip
                              title={adjustment.description}
                              arrow
                              placement="top"
                            >
                              <IconButton
                                aria-label="info"
                                className={styles.infoIconContainer}
                              >
                                <BsInfoSquare className={styles.infoIcon} />
                              </IconButton>
                            </Tooltip>
                          </div>
                          <Typography variant="h4" className={styles.cardValue}>
                            {adjustment.value} <span>{adjustment.unit}</span>
                          </Typography>
                        </CardContent>
                      </Card>
                    ))}
              </div>
              <Card className={styles.card}>
                <CardContent className={styles.echartsContainer}>
                  <LineEcharts
                    option={generateOptionsDefault(
                      data.feed_adjustment.title,
                      data.feed_adjustment.plot
                    )}
                    inlineStyle={{
                      minHeight: "100%",
                      height: "250px",
                    }}
                  />
                </CardContent>
              </Card>
              <Card className={styles.card}>
                <CardContent className={styles.feedInfoCardContainer}>
                  <Typography variant="h2" className={styles.feedInfo}>
                    Feed Info
                  </Typography>
                  <div className={styles.column}>
                    {data.feed_adjustment &&
                      data.feed_adjustment.data.length > 0 &&
                      data.feed_adjustment.data
                        .filter(
                          (filtered) =>
                            filtered.title === "Protein Content" ||
                            filtered.title === "CHB:CP"
                        )
                        .map((adjustment, key) => (
                          <Card
                            className={classNames(styles.card, styles.cardToolTip)}
                            key={key}
                          >
                            <CardContent className={styles.cardContent}>
                              <div className={styles.cardTitleContainer}>
                                <Typography
                                  variant="h3"
                                  className={styles.cardTitle}
                                >
                                  {adjustment.title}
                                </Typography>
                                <Tooltip
                                  title={adjustment.description}
                                  arrow
                                  placement="top"
                                >
                                  <IconButton
                                    aria-label="info"
                                    className={styles.infoIconContainer}
                                  >
                                    <BsInfoSquare className={styles.infoIcon} />
                                  </IconButton>
                                </Tooltip>
                              </div>
                              <Typography variant="h4" className={styles.cardValue}>
                                {adjustment.value} <span>{adjustment.unit}</span>
                              </Typography>
                            </CardContent>
                          </Card>
                        ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>
          <section className={styles.sectionContainer}>
            <Typography variant="h2" className={styles.sectionTitle}>
              Daily Feeding Adjustment
            </Typography>
            <Typography
              variant="h3"
              className={styles.sectionTitle}
              style={{ marginTop: "20px" }}
            >
              Recomendation
            </Typography>
            <div className={styles.dailyFeedingAdjustment}>
              {data.daily_feed_adjustment.data
                .filter((filtered) => filtered.title === "Recommendation")[0]
                .data.filter((data) => data.title === "Feed Ration")
                .map((daily_adjustment, key) => (
                  <Card
                    className={classNames(styles.card, styles.cardToolTip)}
                    key={key}
                  >
                    <CardContent className={styles.cardContent}>
                      <div className={styles.cardTitleContainer}>
                        <Typography variant="h3" className={styles.cardTitle}>
                          {daily_adjustment.title}
                        </Typography>
                        <Tooltip
                          title={daily_adjustment.description}
                          arrow
                          placement="top"
                        >
                          <IconButton
                            aria-label="info"
                            className={styles.infoIconContainer}
                          >
                            <BsInfoSquare className={styles.infoIcon} />
                          </IconButton>
                        </Tooltip>
                      </div>
                      <Typography variant="h4" className={styles.cardValue}>
                        {daily_adjustment.value}
                        <span>{daily_adjustment.unit}</span>
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              {data.daily_feed_adjustment.data
                .filter((filtered) => filtered.title === "Recommendation")[0]
                .data.filter((data) => data.title !== "Feed Ration")
                .map((daily_adjustment, key) => (
                  <Card className={styles.card} key={key}>
                    <CardContent className={styles.cardContent}>
                      <div className={styles.cardTitleContainer}>
                        <Typography variant="h3" className={styles.cardTitle}>
                          {daily_adjustment.title}
                        </Typography>
                      </div>
                      <Typography variant="h4" className={styles.cardValue}>
                        {daily_adjustment.value}{" "}
                        <span>{daily_adjustment.unit}</span>
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
            </div>
          </section>
          <section className={styles.sectionContainer}>
            <div className={styles.realizationHeader}>
              <Typography variant="h3" className={styles.sectionTitle}>
                Realization
              </Typography>
            </div>
            <TableContainer component={Paper}>
              <Table className={styles.table}>
                <TableHead>
                  <TableRow>
                    <TableCell rowSpan="2">Feed Given</TableCell>
                    {Object.keys(
                      data.daily_feed_adjustment.data.filter(
                        (feeds) => feeds.title === "Realization"
                      )[0].data.ration
                    ).map((ration, key) => {
                      return (
                        <TableCell
                          colSpan="2"
                          className={styles.tableCellBorderBottom}
                          key={key}
                        >
                          <div className={styles.tableCellSpaceBetween}>
                            <Typography>Ration {key + 1}</Typography>
                            <ModalAddFeeding
                              data={
                                data.daily_feed_adjustment.data.filter(
                                  (feeds) => feeds.title === "Realization"
                                )[0].data.ration[ration]
                              }
                              onSubmit={refetch}
                              selectedFilter={selectedFilter}
                              index={key}
                            />
                          </div>
                        </TableCell>
                      );
                    })}
                  </TableRow>
                  <TableRow>
                    {Object.keys(
                      data.daily_feed_adjustment.data.filter(
                        (feeds) => feeds.title === "Realization"
                      )[0].data.ration
                    ).map((_, key) => {
                      return (
                        <Fragment key={key}>
                          <TableCell className={styles.tableCellBorderAll}>
                            Realized
                          </TableCell>
                          <TableCell className={styles.tableCellBorderAll}>
                            Leftover (%)
                          </TableCell>
                        </Fragment>
                      );
                    })}
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell className={styles.tableCellBorderAll}>
                      {
                        data.daily_feed_adjustment.data.filter(
                          (data) => data.title === "Realization"
                        )[0].data.feed_given
                      }
                    </TableCell>
                    {Object.keys(
                      data.daily_feed_adjustment.data.filter(
                        (feeds) => feeds.title === "Realization"
                      )[0].data.ration
                    ).map((ration, key) => {
                      return (
                        <Fragment key={key}>
                          <TableCell className={styles.tableCellBorderAll}>
                            {
                              data.daily_feed_adjustment.data.filter(
                                (feeds) => feeds.title === "Realization"
                              )[0].data.ration[ration].value[0].value
                            }
                          </TableCell>
                          <TableCell className={styles.tableCellBorderAll}>
                            {
                              data.daily_feed_adjustment.data.filter(
                                (feeds) => feeds.title === "Realization"
                              )[0].data.ration[ration].value[1].value
                            }
                          </TableCell>
                        </Fragment>
                      );
                    })}
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </section>
        </Fragment>
      )}
    </Fragment>
  );
};

export default Feeding;
