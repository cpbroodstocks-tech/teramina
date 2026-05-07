import { Fragment } from "react";
import { Typography, TextField, Button, CircularProgress } from "@mui/material";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { StaticDatePicker } from "@mui/x-date-pickers/StaticDatePicker";
import classNames from "classnames";
import { useStyles } from "features/farm/new-cycle/styles";
import { useTranslation } from "react-i18next";

const NewCycle = (props) => {
  const {
    formik,
    formTitle = "CREATE_NEW_CYCLE",
    actionText = "SUBMIT",
    loading = false,
    isModalComponent = false,
    handleBack,
  } = props;

  const { t } = useTranslation();
  const { classes: styles } = useStyles();

  return (
    <Fragment>
      <form className={styles.container} onSubmit={formik.handleSubmit}>
        <Typography variant="h5" className={styles.title}>
          {t(formTitle)}
        </Typography>
        <Typography
          variant="h6"
          className={classNames(styles.label, styles.requiredLabel)}
        >
          {t("CYCLE_NAME")}
        </Typography>
        <TextField
          variant="outlined"
          className={styles.input}
          error={!!formik.formState.errors.name}
          helperText={formik.formState.errors.name?.message}
          {...formik.register("name")}
        />
        <Typography
          variant="h6"
          className={classNames(styles.label, styles.requiredLabel)}
        >
          {t("CYCLE_START_DATE")}
        </Typography>
        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <StaticDatePicker
            displayStaticWrapperAs="desktop"
            openTo="day"
            inputFormat="DD/MM/YYYY"
            onChange={(newValue) => formik.setValue("date", newValue)}
            className={styles.calendar}
            value={formik.watch("date")}
            renderInput={(params) => <TextField {...params} />}
          />
        </LocalizationProvider>
        <div className={styles.btnContainer}>
          {handleBack && (
            <Button
              variant="contained"
              className={styles.btnBack}
              onClick={() => {
                handleBack();
              }}
              classes={{
                disabled: styles.btnBackDisabled,
              }}
              disabled={loading}
            >
              {t("BACK")}
            </Button>
          )}
          {isModalComponent && (
            <Button
              type="submit"
              variant="contained"
              className={styles.btnSubmit}
              disabled={formik.formState.isSubmitting}
            >
              {formik.formState.isSubmitting ? (
                <CircularProgress
                  color="inherit"
                  classes={{ root: styles.circular }}
                />
              ) : (
                t(actionText)
              )}
            </Button>
          )}
          {!isModalComponent && (
            <Button
              type="submit"
              variant="contained"
              className={styles.btnSubmit}
              disabled={loading}
            >
              {loading ? (
                <CircularProgress
                  color="inherit"
                  classes={{ root: styles.circular }}
                />
              ) : (
                <>{t(actionText)}</>
              )}
            </Button>
          )}
        </div>
      </form>
    </Fragment>
  );
};

export default NewCycle;
