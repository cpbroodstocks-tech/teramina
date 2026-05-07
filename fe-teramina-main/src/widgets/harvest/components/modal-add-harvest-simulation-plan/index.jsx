import { Fragment } from "react";
import { Button, Dialog, DialogContent, FormGroup, TextField, Typography } from "@mui/material";
import { useModal } from "hooks/useModal";
import { useStyles } from "widgets/harvest/components/modal-add-harvest-simulation-plan/styles";
import {
  HARVEST_FORMAT,
  generateHarvestInitialValues,
} from "widgets/harvest/hooks";
import { useAddHarverstSimulationPlanForm } from "widgets/harvest/components/modal-add-harvest-simulation-plan/hooks";
import { useToastStore } from "store/toast.store";
import { useCreateHarvestSimulation } from "widgets/harvest/queries";
import classNames from "classnames";
import { useTranslation } from "react-i18next";

const AddHarvestSimulationPlan = ({
  selectedFilter,
  simulationPlan,
  setSimulationPlan,
  currentData,
  onClose,
  MAXIMUM_HARVEST_SIMULATION,
}) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { setToast: toast } = useToastStore();
  const { mutateAsync } = useCreateHarvestSimulation(selectedFilter.cycle_id);

  const handleAddSimulationPlan = async (values) => {
    if (simulationPlan.length >= MAXIMUM_HARVEST_SIMULATION) return;
    const body = { ...values };
    Object.keys(body).forEach((k) => {
      body[k] = { doc: parseInt(body[k].doc, 10), biomass: parseInt(body[k].biomass, 10) };
    });
    try {
      const result = await mutateAsync(body);
      setSimulationPlan((prev) => [...prev, result]);
      await onClose();
      toast({ open: true, variant: "success", text: t("ADD_DATA_SUCCESS_MESSAGE") });
    } catch (err) {
      const errorMessage = err.response?.data?.message || t("ADD_DATA_FAILED_MESSAGE");
      toast({ open: true, variant: "error", text: errorMessage });
    }
  };

  const harvestInitialValues = generateHarvestInitialValues(currentData.rows);

  const { handleSubmit, register, errors, isSubmitting, initialValues } = useAddHarverstSimulationPlanForm({
    initialValues: {
      ...harvestInitialValues,
      cycle_info: currentData.cycle_info,
    },
    onSubmit: handleAddSimulationPlan,
  });

  return (
    <Fragment>
      <form className={styles.container} onSubmit={handleSubmit}>
        <Typography variant="h5" className={styles.title}>
          {t("HARVEST_SIMULATION_PLAN")}
        </Typography>
        {Object.keys(HARVEST_FORMAT).map((key, i) => (
          <div className={styles.formRow} key={i}>
            <Typography className={styles.titleFieldUppercase}>
              {key.replace(/[a-z](?=\d)|\d(?=[a-z])/gi, "$& ")}
            </Typography>
            <FormGroup className={styles.formGroup}>
              <div className={styles.formInputGroup}>
                <Typography
                  className={classNames(
                    styles.labelField,
                    styles.requiredLabel
                  )}
                >
                  DOC
                </Typography>
                <TextField
                  {...register(`${key}.doc`)}
                  disabled={!!initialValues[key].doc}
                  type="number"
                  variant="outlined"
                />
                {errors[key] && (
                  <Typography className={styles.errorMessage}>
                    {errors[key].doc?.message}
                  </Typography>
                )}
              </div>
              <div className={styles.formInputGroup}>
                <Typography
                  className={classNames(
                    styles.labelField,
                    styles.requiredLabel
                  )}
                >
                  {t("HARVEST_BIOMASS")}
                </Typography>
                <TextField
                  {...register(`${key}.biomass`)}
                  disabled={!!initialValues[key].biomass}
                  type="number"
                  variant="outlined"
                />
                {errors[key] && (
                  <Typography className={styles.errorMessage}>
                    {errors[key].biomass?.message}
                  </Typography>
                )}
              </div>
            </FormGroup>
          </div>
        ))}
        <div className={styles.btnContainer}>
          <Button
            fullWidth
            type="submit"
            className={styles.buttonAction}
            disabled={isSubmitting}
          >
            {isSubmitting ? t("LOADING") : t("SUBMIT")}
          </Button>
        </div>
      </form>
    </Fragment>
  );
};

const ModalAddHarvestSimulationPlan = (props) => {
  const { t } = useTranslation();
  const { open, onOpen, onClose } = useModal();
  return (
    <Fragment>
      <Button onClick={onOpen} sx={{ color: "#161616", minWidth: "unset !important", background: "rgba(71, 77, 164, 0.32)", marginRight: "5px", borderRadius: "6px", padding: "10.5px", "&:hover": { color: "#161616", background: "rgba(71, 77, 164, 0.6)" }, "& svg": { width: "20px", height: "20px" } }}>{t("ADD_SIMULATION")}</Button>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
        <DialogContent sx={{ padding: "0px !important" }}>
          <AddHarvestSimulationPlan {...props} onClose={onClose} />
        </DialogContent>
      </Dialog>
    </Fragment>
  );
};

export default ModalAddHarvestSimulationPlan;
