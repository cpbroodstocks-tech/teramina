import { Fragment } from "react";
import {
  Button,
  Box,
  Dialog,
  DialogContent,
  Typography,
  RadioGroup,
  Radio,
  FormControlLabel,
  FormGroup,
  TextField,
} from "@mui/material";
import classNames from "classnames";
import { useStyles } from "widgets/harvest/components/modal-edit-harvest-record/styles";
import { useEditHarvestRecordForm } from "widgets/harvest/components/modal-edit-harvest-record/hooks";
import { useModal } from "hooks/useModal";
import { generateHarvestInitialValues } from "widgets/harvest/hooks";
import { useToastStore } from "store/toast.store";
import { useTranslation } from "react-i18next";
import { useAddHarvestRecord } from "widgets/harvest/queries";

const EditHarvest = ({ currentData, selectedFilter, refetch, harvestKey }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { setToast: toast } = useToastStore();
  const { mutateAsync } = useAddHarvestRecord(selectedFilter.cycle_id);

  const initialValues = currentData.rows.filter((data) => {
    if (harvestKey === "final") {
      return `${data.harvest_type}` === "final";
    }
    return `${data.harvest_type}${data.harvest_no}` === harvestKey;
  })[0];

  const formik = useEditHarvestRecordForm({
    initialValues: initialValues,
    onSubmit: async (values) => {
      try {
        const harvestInitialValues = generateHarvestInitialValues(currentData.rows);
        const body = {
          ...harvestInitialValues,
          [`${harvestKey}`]: {
            doc: parseInt(values.harvest_doc, 10),
            biomass: parseInt(values.harvest_biomass, 10),
            revenue: parseInt(values.harvest_revenue, 10),
          },
        };
        await mutateAsync(body);
        toast({ open: true, variant: "success", text: t("ADD_DATA_SUCCESS_MESSAGE") });
        if (refetch) refetch();
      } catch {
        toast({ open: true, variant: "error", text: t("ADD_DATA_FAILED_MESSAGE") });
      }
    },
  });

  return (
    <Box className={styles.formContainer}>
      <Typography variant="h5" className={styles.title}>
        {t("ADD_HARVEST_DATA")}
      </Typography>
      <div className={styles.formWrapper}>
        <form onSubmit={formik.handleSubmit}>
          <FormGroup>
            <Typography
              variant="h6"
              className={classNames(styles.label, styles.requiredLabel)}
            >
              {t("HARVEST_TYPE")}
            </Typography>
            <div className={styles.radioContainer}>
              <RadioGroup
                aria-labelledby="harvest-radio-buttons-group-label"
                name="harvest_type"
                onChange={(e) => formik.setValue("harvest_type", e.target.value)}
                value={formik.watch("harvest_type")}
              >
                <FormControlLabel
                  value="partial"
                  label="Partial"
                  disabled={formik.watch("harvest_type") !== "partial"}
                  control={<Radio />}
                />
                <FormControlLabel
                  value="final"
                  label="Final"
                  disabled={formik.watch("harvest_type") !== "final"}
                  control={<Radio />}
                />
              </RadioGroup>
            </div>
          </FormGroup>
          <FormGroup className={styles.formInput}>
            <Typography
              variant="h6"
              className={classNames(styles.label, styles.requiredLabel)}
            >
              DOC
            </Typography>
            <TextField {...formik.register("harvest_doc")} />
          </FormGroup>
          <FormGroup className={styles.formInput}>
            <Typography
              variant="h6"
              className={classNames(styles.label, styles.requiredLabel)}
            >
              {t("HARVEST_BIOMASS")}
            </Typography>
            <TextField {...formik.register("harvest_biomass")} />
          </FormGroup>
          <FormGroup className={styles.formInput}>
            <Typography
              variant="h6"
              className={classNames(styles.label, styles.requiredLabel)}
            >
              {t("HARVEST_REVENUE")}
            </Typography>
            <TextField {...formik.register("harvest_revenue")} />
          </FormGroup>
          <Button
            fullWidth
            type="submit"
            className={styles.buttonAction}
            disabled={formik.formState.isSubmitting}
          >
            {formik.formState.isSubmitting ? t("LOADING") : t("SUBMIT")}
          </Button>
        </form>
      </div>
    </Box>
  );
};

const ModalEditHarvestRecord = (props) => {
  const { t } = useTranslation();
  const { open, onOpen, onClose } = useModal();
  return (
    <Fragment>
      <Button onClick={onOpen} sx={{ color: "#161616", minWidth: "unset !important", background: "rgba(71, 77, 164, 0.32)", marginRight: "5px", borderRadius: "6px", padding: "10.5px", "&:hover": { color: "#161616", background: "rgba(71, 77, 164, 0.6)" }, "& svg": { width: "20px", height: "20px" } }}>{t("EDIT_HARVEST_RECORD")}</Button>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
        <DialogContent sx={{ padding: "0px !important" }}>
          <EditHarvest {...props} onClose={onClose} />
        </DialogContent>
      </Dialog>
    </Fragment>
  );
};

export default ModalEditHarvestRecord;
