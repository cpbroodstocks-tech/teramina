import { Fragment } from "react";
import { useFilter } from "features/filter/harvest/hooks";
import Filter from "features/filter/harvest";
import { useTranslation } from "react-i18next";
import { Typography } from "@mui/material";
import { useStyles } from "widgets/harvest/styles";
import Error from "components/error";
import Loader from "components/loader";
import Empty from "components/empty";
import HarvestRecord from "widgets/harvest/components/harvest-record";
import HarvestRecomendationTable from "widgets/harvest/components/harvest-recomendation";
import HarvestSimulation from "widgets/harvest/components/harvest-simulation";

const Harvest = () => {
  const { t } = useTranslation();
  const { loading, filter, data, error, form, selectedFilter, refetch, onFilterChange } = useFilter(["/harvest/harvest-record-data", "/harvest/harvest-recommendation"]);
  const { classes: styles } = useStyles();

  return (
    <Fragment>
      <Typography variant="h1" sx={{ mb: "15px", fontSize: 40, textTransform: "uppercase" }}>{t("MENU.HARVEST")}</Typography>
      <Filter data={data} filter={filter} form={form} onFilterChange={onFilterChange} />
      {loading && <Loader />}
      {error && <Error />}
      {!loading && !error && !Object.keys(data).length && <Empty />}
      {!loading && !error && Object.keys(data).length > 0 && (
        <Fragment>
          <section className={styles.sectionWrapper}>
            <HarvestRecomendationTable data={data.harvestRecomendation} />
          </section>
          <section className={styles.sectionWrapper}>
            <HarvestRecord
              data={data.harvestRecord}
              selectedFilter={selectedFilter}
              refetch={refetch}
            />
          </section>
          <section className={styles.sectionWrapper}>
            <HarvestSimulation
              data={data.harvestRecord}
              selectedFilter={selectedFilter}
            />
          </section>
        </Fragment>
      )}
    </Fragment>
  );
};

export default Harvest;
