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
import { useStyles } from "widgets/harvest/components/modal-add-harvest-record/styles";
import { useAddHarvestRecordForm } from "widgets/harvest/components/modal-add-harvest-record/hooks";
import { useModal } from "hooks/useModal";
import {
  HARVEST_LENGTH,
  generateBody,
  generateHarvestInitialValues,
} from "widgets/harvest/hooks";
import classNames from "classnames";
import { useToastStore } from "store/toast.store";
import { useTranslation } from "react-i18next";
import { useAddHarvestRecord } from "widgets/harvest/queries";

const AddHarvest = ({ currentData, selectedFilter, refetch }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { setToast: toast } = useToastStore();
  const { mutateAsync } = useAddHarvestRecord(selectedFilter.cycle_id);
  const form = useAddHarvestRecordForm({
    onSubmit: async (values) => {
      try {
        const harvestInitialValues = generateHarvestInitialValues(currentData.rows);
        const body = generateBody(harvestInitialValues, currentData.rows, values);
        await mutateAsync(body);
        toast({ open: true, variant: "success", text: t("ADD_DATA_SUCCESS_MESSAGE") });
        if (refetch) refetch();
      } catch (err) {
        const errorMessage = err.response?.data?.message || t("ADD_DATA_FAILED_MESSAGE");
        toast({ open: true, variant: "error", text: errorMessage });
      }
    },
  });

  return (
    <Box className={styles.formContainer}>
      <form onSubmit={form.handleSubmit}>
        <FormGroup>
          <Typography variant="h5" className={styles.title}>
            {t("ADD_HARVEST_DATA")}
          </Typography>
          <Typography className={styles.labelField}>
            {t("HARVEST_TYPE")}
          </Typography>
          <div className={styles.radioContainer}>
            <RadioGroup
              aria-labelledby="harvest-radio-buttons-group-label"
              name="harvest_type"
              onChange={(e) => form.setValue("harvest_type", e.target.value)}
              value={form.watch("harvest_type")}
            >
              <FormControlLabel
                value="partial"
                label="Partial"
                disabled={
                  currentData.rows.filter(
                    (data) => data.harvest_type === "partial"
                  ).length >=
                  HARVEST_LENGTH - 1
                }
                control={<Radio />}
              />
              <FormControlLabel
                value="final"
                label="Final"
                control={<Radio />}
              />
            </RadioGroup>
          </div>
        </FormGroup>
        <FormGroup className={styles.formInput}>
          <Typography
            className={classNames(styles.labelField, styles.requiredLabel)}
          >
            DOC
          </Typography>
          <TextField {...form.register("harvest_doc")} />
        </FormGroup>
        <FormGroup className={styles.formInput}>
          <Typography
            className={classNames(styles.labelField, styles.requiredLabel)}
          >
            {t("HARVEST_BIOMASS")}
          </Typography>
          <TextField {...form.register("harvest_biomass")} />
        </FormGroup>
        <FormGroup className={styles.formInput}>
          <Typography
            className={classNames(styles.labelField, styles.requiredLabel)}
          >
            {t("HARVEST_REVENUE")}
          </Typography>
          <TextField {...form.register("harvest_revenue")} />
        </FormGroup>
        <div className={styles.btnContainer}>
          <Button fullWidth type="submit" className={styles.buttonAction}>
            {t("SUBMIT")}
          </Button>
        </div>
      </form>
    </Box>
  );
};

const ModalAddHarvestRecord = (props) => {
  const { t } = useTranslation();
  const { open, onOpen, onClose } = useModal();
  return (
    <Fragment>
      <Button onClick={onOpen} sx={{ color: "#161616", minWidth: "unset !important", background: "rgba(71, 77, 164, 0.32)", marginRight: "5px", borderRadius: "6px", padding: "10.5px", "&:hover": { color: "#161616", background: "rgba(71, 77, 164, 0.6)" }, "& svg": { width: "20px", height: "20px" } }}>{t("ADD_HARVEST_RECORD")}</Button>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
        <DialogContent sx={{ padding: "0px !important" }}>
          <AddHarvest {...props} onClose={onClose} />
        </DialogContent>
      </Dialog>
    </Fragment>
  );
};

export default ModalAddHarvestRecord;
