import { Fragment } from "react";
import {
  Typography,
  TextField,
  Button,
  Radio,
  RadioGroup,
  FormControlLabel,
  CircularProgress,
} from "@mui/material";
import classNames from "classnames";
import { useStyles } from "features/farm/new-pond/styles";
import { constructionList, shapeList } from "features/farm/new-pond/define";
import { useTranslation } from "react-i18next";

const NewPond = (props) => {
  const {
    formik,
    formTitle = "CREATE_NEW_POND",
    actionText = "SUBMIT",
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
          {t("POND_NAME")}
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
          {t("POND_SIZE")} <span style={{ fontSize: "0.75em" }}>(m&sup2;)</span>
        </Typography>
        <TextField
          variant="outlined"
          className={styles.input}
          error={!!formik.formState.errors.size}
          helperText={formik.formState.errors.size?.message}
          type="number"
          {...formik.register("size")}
        />
        <Typography
          variant="h6"
          className={classNames(styles.label, styles.requiredLabel)}
        >
          {t("POND_CONSTRUCTION")}
        </Typography>
        <div className={styles.radioContainer}>
          <RadioGroup
            aria-labelledby="construction-radio-buttons-group-label"
            defaultValue="hdpe"
            name="construction"
            onChange={({ target }) => {
              const selectedLabel = constructionList.filter(
                (construction) => construction.value === target.value
              );
              if (target.value !== "other")
                formik.setValue("otherConstructionLabel", "");
              formik.setValue("construction", {
                label: selectedLabel[0].label,
                value: target.value,
              });
            }}
            value={formik.watch("construction").value}
          >
            {constructionList.map((list, key) => {
              if (list.value === "other") {
                return (
                  <div className={styles.isOtherRadioValue} key={key}>
                    <FormControlLabel
                      value={list.value}
                      control={<Radio />}
                      label={list.label}
                    />
                    <div className="other-value-wrapper">
                      <TextField
                        variant="outlined"
                        className={styles.input}
                        error={!!formik.formState.errors.otherConstructionLabel}
                        helperText={formik.formState.errors.otherConstructionLabel?.message}
                        disabled={formik.watch("construction").value !== "other"}
                        {...formik.register("otherConstructionLabel")}
                      />
                    </div>
                  </div>
                );
              }
              return (
                <FormControlLabel
                  key={key}
                  value={list.value}
                  control={<Radio />}
                  label={list.label}
                />
              );
            })}
          </RadioGroup>
        </div>
        <Typography
          variant="h6"
          className={classNames(styles.label, styles.requiredLabel)}
        >
          {t("POND_SHAPE")}
        </Typography>
        <div className={styles.radioContainer}>
          <RadioGroup
            aria-labelledby="shape-radio-buttons-group-label"
            defaultValue="persegi"
            name="shape"
            onChange={({ target }) => {
              const selectedLabel = shapeList.filter(
                (shape) => shape.value === target.value
              );
              if (target.value !== "other") {
                formik.setValue("otherShapeLabel", "");
              }
              formik.setValue("shape", {
                label: selectedLabel[0].label,
                value: target.value,
              });
            }}
            value={formik.watch("shape").value}
          >
            {shapeList.map((list, key) => {
              if (list.value === "other") {
                return (
                  <div className={styles.isOtherRadioValue} key={key}>
                    <FormControlLabel
                      value={list.value}
                      control={<Radio />}
                      label={list.label}
                    />
                    <div className="other-value-wrapper">
                      <TextField
                        variant="outlined"
                        className={styles.input}
                        error={!!formik.formState.errors.otherShapeLabel}
                        helperText={formik.formState.errors.otherShapeLabel?.message}
                        disabled={formik.watch("shape").value !== "other"}
                        {...formik.register("otherShapeLabel")}
                      />
                    </div>
                  </div>
                );
              }
              return (
                <FormControlLabel
                  key={key}
                  value={list.value}
                  control={<Radio />}
                  label={list.label}
                />
              );
            })}
          </RadioGroup>
        </div>
        <div className={styles.btnContainer}>
          {handleBack && (
            <Button
              variant="contained"
              className={styles.btnBack}
              onClick={() => {
                handleBack && handleBack();
              }}
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
                <>{t(actionText)}</>
              )}
            </Button>
          )}
          {!isModalComponent && (
            <Button
              type="submit"
              variant="contained"
              className={styles.btnSubmit}
            >
              {t(actionText)}
            </Button>
          )}
        </div>
      </form>
    </Fragment>
  );
};

export default NewPond;
