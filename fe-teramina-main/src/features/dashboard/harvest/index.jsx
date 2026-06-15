import { Fragment } from "react";
import { useFilter } from "features/filter/harvest/hooks";
import { useTranslation } from "react-i18next";
import { useStyles } from "widgets/harvest/styles";
import Error from "components/error";
import Loader from "components/loader";
import Empty from "components/empty";
import HarvestRecord from "widgets/harvest/components/harvest-record";
import HarvestRecomendationTable from "widgets/harvest/components/harvest-recomendation";
import HarvestSimulation from "widgets/harvest/components/harvest-simulation";
import PageHeader from "components/page-header";

const Harvest = () => {
  const { t } = useTranslation();
  const { loading, data, error, selectedFilter, refetch } = useFilter(["/harvest/harvest-record-data", "/harvest/harvest-recommendation"]);
  const { classes: styles } = useStyles();

  return (
    <Fragment>
      <PageHeader title={t("MENU.HARVEST")} description={t("PAGE_DESCRIPTION.HARVEST")} />
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
