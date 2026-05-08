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
    form,
    formTitle = "CREATE_NEW_POND",
    actionText = "SUBMIT",
    isModalComponent = false,
    handleBack,
  } = props;

  const { t } = useTranslation();
  const { classes: styles } = useStyles();

  return (
    <Fragment>
      <form className={styles.container} onSubmit={form.handleSubmit}>
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
          error={!!form.formState.errors.name}
          helperText={form.formState.errors.name?.message}
          {...form.register("name")}
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
          error={!!form.formState.errors.size}
          helperText={form.formState.errors.size?.message}
          type="number"
          {...form.register("size")}
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
                form.setValue("otherConstructionLabel", "");
              form.setValue("construction", {
                label: selectedLabel[0].label,
                value: target.value,
              });
            }}
            value={form.watch("construction").value}
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
                        error={!!form.formState.errors.otherConstructionLabel}
                        helperText={form.formState.errors.otherConstructionLabel?.message}
                        disabled={form.watch("construction").value !== "other"}
                        {...form.register("otherConstructionLabel")}
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
                form.setValue("otherShapeLabel", "");
              }
              form.setValue("shape", {
                label: selectedLabel[0].label,
                value: target.value,
              });
            }}
            value={form.watch("shape").value}
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
                        error={!!form.formState.errors.otherShapeLabel}
                        helperText={form.formState.errors.otherShapeLabel?.message}
                        disabled={form.watch("shape").value !== "other"}
                        {...form.register("otherShapeLabel")}
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
              disabled={form.formState.isSubmitting}
            >
              {form.formState.isSubmitting ? (
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
