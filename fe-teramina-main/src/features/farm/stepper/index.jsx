import { Fragment, useState } from "react";
import classNames from "classnames";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Step,
  Stepper,
  StepLabel,
} from "@mui/material";
import { useToastStore } from "store/toast.store";
import { useStyles } from "features/farm/stepper/style";
import { useAddFarm } from "features/farm/queries";
import { useAddPond } from "features/pond/queries";
import { useAddCycle } from "features/cycle/queries";
import NewFarm from "features/farm/new-farm";
import Start from "features/farm/start";
import NewPond from "features/farm/new-pond";
import NewCycle from "features/farm/new-cycle";
import { useNewFarmForm } from "features/farm/new-farm/hooks";
import { useNewPondForm } from "features/farm/new-pond/hooks";
import { useNewCycleForm } from "features/farm/new-cycle/hooks";
import dayjs from "dayjs";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

const wizardInitial = { farm: {}, pond: {}, cycle: {} };

const FarmWizard = ({ onDoneSubmit }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { setToast: toast } = useToastStore();
  const navigate = useNavigate();
  const [open, setOpen] = useState(() => false);
  const [activeStep, setActiveStep] = useState(() => 0);
  const [wizard, setWizard] = useState(() => wizardInitial);

  const { mutateAsync: addFarm, isPending: addingFarm } = useAddFarm();
  const { mutateAsync: addPond, isPending: addingPond } = useAddPond();
  const { mutateAsync: addCycle, isPending: addingCycle } = useAddCycle();
  const loading = addingFarm || addingPond || addingCycle;

  const handleNextStep = () => setActiveStep((prev) => prev + 1);
  const handlePreviousStep = () => setActiveStep((prev) => prev - 1);

  const handleNewFarmSubmit = async (values) => {
    setWizard((prev) => ({ ...prev, farm: values }));
    return handleNextStep();
  };

  const handleNewPondSubmit = async (values) => {
    setWizard((prev) => ({ ...prev, pond: values }));
    return handleNextStep();
  };

  const handleNewCycleSubmit = async (values) => {
    setWizard((prev) => ({ ...prev, cycle: values }));
    setOpen(true);
  };

  const formikFarm = useNewFarmForm({ onSubmit: handleNewFarmSubmit });
  const formikPond = useNewPondForm({ onSubmit: handleNewPondSubmit });
  const formikCycle = useNewCycleForm({ onSubmit: handleNewCycleSubmit });

  const handleSubmitAllForm = async () => {
    setOpen(false);
    try {
      const wizardFarmRegionState = {
        provinsi: JSON.parse(wizard.farm.provinsi),
        kabupaten: JSON.parse(wizard.farm.kabupaten),
        kecamatan: JSON.parse(wizard.farm.kecamatan),
        kelurahan: JSON.parse(wizard.farm.kelurahan),
      };

      const farm = await addFarm({
        name: wizard.farm.name,
        location: `${wizardFarmRegionState.kelurahan.name}, ${wizardFarmRegionState.kecamatan.name}, ${wizardFarmRegionState.kabupaten.name}, ${wizardFarmRegionState.provinsi.name}`,
      });

      const pond = await addPond({
        farm_id: farm.id,
        name: wizard.pond.name,
        size: wizard.pond.size,
        pond_construction: wizard.pond.construction.value === "other" ? wizard.pond.otherConstructionLabel : wizard.pond.construction.label,
        pond_shape: wizard.pond.shape.value === "other" ? wizard.pond.otherShapeLabel : wizard.pond.shape.label,
      });

      const date = dayjs(wizard.cycle.date).format("MM/DD/YYYY");
      const cycle = await addCycle({ pond_id: pond.id, name: wizard.cycle.name, start_date: date });

      toast({ open: true, variant: "success", text: t("ADD_DATA_SUCCESS_MESSAGE") });
      if (onDoneSubmit) {
        onDoneSubmit();
      } else {
        navigate(`/dashboard/cycle/detail/${cycle.id}`);
      }
    } catch {
      toast({ open: true, variant: "error", text: t("ADD_DATA_FAILED_MESSAGE") });
    }
  };

  return (
    <Fragment>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">{t("FARM_DATA")}</DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            {t("ADD_NEW_FARM")}?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>{t("NO")}</Button>
          <Button
            className={styles.btnYesModal}
            variant="contained"
            onClick={() => handleSubmitAllForm()}
          ></Button>
        </DialogActions>
      </Dialog>
      <Stepper activeStep={activeStep} label={null} connector={null}>
        <Step
          className={classNames(
            styles.stepper,
            0 === activeStep && styles.stepperActive
          )}
        >
          <StepLabel classes={{ iconContainer: styles.iconStepper }}>
            <Start handleBack={handlePreviousStep} onSubmit={handleNextStep} />
          </StepLabel>
        </Step>
        <Step
          className={classNames(
            styles.stepper,
            1 === activeStep && styles.stepperActive
          )}
        >
          <StepLabel classes={{ iconContainer: styles.iconStepper }}>
            <NewFarm handleBack={handlePreviousStep} form={formikFarm} />
          </StepLabel>
        </Step>
        <Step
          className={classNames(
            styles.stepper,
            2 === activeStep && styles.stepperActive
          )}
        >
          <StepLabel classes={{ iconContainer: styles.iconStepper }}>
            <NewPond handleBack={handlePreviousStep} form={formikPond} />
          </StepLabel>
        </Step>
        <Step
          className={classNames(
            styles.stepper,
            3 === activeStep && styles.stepperActive
          )}
        >
          <StepLabel classes={{ iconContainer: styles.iconStepper }}>
            <NewCycle
              loading={loading}
              handleBack={handlePreviousStep}
              form={formikCycle}
            />
          </StepLabel>
        </Step>
      </Stepper>
    </Fragment>
  );
};

export default FarmWizard;
