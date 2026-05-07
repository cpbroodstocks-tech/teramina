import { FormControl, Typography, TextField, Button } from "@mui/material";
import { useRationForm } from "features/feeding/new-ration/hooks";
import { Fragment } from "react";
import { useStyles } from "features/feeding/new-ration/styles";
import classNames from "classnames";
import { useToastStore } from "store/toast.store";
import { useTranslation } from "react-i18next";
import { useSaveFeedingRation } from "features/feeding/queries";

const NewRationForm = ({ initialValue, onSubmit, selectedFilter, onClose }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { setToast: toast } = useToastStore();
  const { mutateAsync } = useSaveFeedingRation();

  const formik = useRationForm({
    initialValues: {
      ration_id: initialValue.id,
      realized: initialValue.value[0].value,
      leftover: initialValue.value[1].value,
      ration_number: initialValue.ration_number,
    },
    onSubmit: async (values) => {
      try {
        await mutateAsync({
          cycle_id: selectedFilter.cycle_id,
          ration_id: values.ration_id || undefined,
          date: selectedFilter.date,
          ration_number: values.ration_number,
          feed_given: values.feed_given,
          feed_leftover: values.feed_leftover,
        });
        await onSubmit();
        onClose && (await onClose());
        toast({ open: true, variant: "success", text: t("ADD_DATA_SUCCESS_MESSAGE") });
      } catch (err) {
        const errorMessage = err.response?.data?.message || t("ADD_DATA_FAILED_MESSAGE");
        toast({ open: true, variant: "error", text: errorMessage });
      }
    },
  });

  return (
    <Fragment>
      <form className={styles.formContainer} onSubmit={formik.handleSubmit}>
        <Typography className={styles.titleForm} variant="h3">
          {t("INPUT_FEEDING_DATA")}
        </Typography>
        <FormControl fullWidth>
          <Typography className={styles.titleField}>
            {t("RATION_NUMBER")}
          </Typography>
          <TextField
            fullWidth
            disabled
            variant="outlined"
            error={!!formik.formState.errors.ration_number}
            helperText={formik.formState.errors.ration_number?.message}
            {...formik.register("ration_number")}
          />
        </FormControl>
        <FormControl fullWidth>
          <Typography
            className={classNames(styles.titleField, styles.requiredLabel)}
          >
            {t("FEED_GIVEN")}
          </Typography>
          <TextField
            fullWidth
            variant="outlined"
            error={!!formik.formState.errors.feed_given}
            helperText={formik.formState.errors.feed_given?.message}
            {...formik.register("feed_given")}
          />
        </FormControl>
        <FormControl fullWidth>
          <Typography className={styles.titleField}>
            {t("FEED_LEFTOVER")}
          </Typography>
          <TextField
            fullWidth
            variant="outlined"
            placeholder={t("OPTIONAL")}
            error={!!formik.formState.errors.feed_leftover}
            helperText={formik.formState.errors.feed_leftover?.message}
            {...formik.register("feed_leftover")}
          />
        </FormControl>
        <FormControl fullWidth>
          <Button
            fullWidth
            className={styles.buttonAction}
            type="submit"
            disabled={formik.formState.isSubmitting}
          >
            {formik.formState.isSubmitting ? t("LOADING") : t("SUBMIT")}
          </Button>
        </FormControl>
      </form>
    </Fragment>
  );
};

export default NewRationForm;
