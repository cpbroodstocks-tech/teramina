import { Fragment, useState } from "react";
import { useStyles } from "widgets/harvest/components/harvest-simulation/styles";
import { Button, Typography } from "@mui/material";
import ModalAddHarvestSimulationPlan from "widgets/harvest/components/modal-add-harvest-simulation-plan/index";
import TableHarvestSimulation from "widgets/harvest/components/table-harvest-simulation";
import { useTranslation } from "react-i18next";

const MAXIMUM_HARVEST_SIMULATION = 2;

const HarvestSimulation = ({ data, selectedFilter }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const [simulationPlan, setSimulationPlan] = useState(() => []);

  const handleRemoveSimulationPlan = (key) => {
    setSimulationPlan((previousValue) =>
      previousValue.filter((_, i) => key !== i)
    );
  };

  return (
    <Fragment>
      <div className={styles.sectionTitle}>
        <Typography variant="h3">{t("HARVEST_SIMULATION_PLAN")}</Typography>
        {simulationPlan.length < MAXIMUM_HARVEST_SIMULATION && (
          <ModalAddHarvestSimulationPlan
            selectedFilter={selectedFilter}
            simulationPlan={simulationPlan}
            setSimulationPlan={setSimulationPlan}
            currentData={data}
            MAXIMUM_HARVEST_SIMULATION={MAXIMUM_HARVEST_SIMULATION}
          />
        )}
      </div>

      {simulationPlan.length > 0 ? (
        <>
          {simulationPlan.map((simulation, key) => (
            <div className={styles.harvestSimulationPlan} key={key}>
              <div className={styles.simulationPlanTitle}>
                <Typography variant="h3">
                  {t("SIMULATION_RESULT")} {key + 1}
                </Typography>
                <Button
                  className={styles.buttonAction}
                  onClick={() => handleRemoveSimulationPlan(key)}
                >
                  {t("REMOVE_SIMULATION")}
                </Button>
              </div>
              <TableHarvestSimulation data={simulation} />
            </div>
          ))}
        </>
      ) : (
        <div className={styles.contentEmpty}>
          <div className={styles.lgEmpty}>
            <img src="/assets/images/empty-harvest-plan.png" alt="empty" />
          </div>
        </div>
      )}
    </Fragment>
  );
};

export default HarvestSimulation;
