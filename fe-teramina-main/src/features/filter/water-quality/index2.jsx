import { Fragment } from "react";
import {
  MenuItem,
  FormControl,
  Select,
  Button,
  OutlinedInput,
} from "@mui/material";
import { useStyles } from "features/filter/harvest/styles";
import {
  StartDatePickerPopUp,
  EndDatePickerPopUp,
} from "features/filter/water-quality/components/datepicker-popup";
import { useTranslation } from "react-i18next";

const Filter = ({ filter, formik, onFilterChange }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { farms, ponds, cycles, daterange, variables } = filter;

  return (
    <Fragment>
      <form onSubmit={formik.handleSubmit}>
        <div className={styles.filterWrapper}>
          <FormControl className={styles.filterFormControl} size="small">
            <Select
              displayEmpty
              name="farm_id"
              defaultValue={""}
              value={formik.values.farm_id}
              onChange={(e) => onFilterChange("farm_id", e.target.value)}
              className={styles.filterSelectOption}
            >
              <MenuItem disabled value="">
                <em>{t("FARM")}</em>
              </MenuItem>
              {farms &&
                farms.map((farm, key) => (
                  <MenuItem value={farm.id} key={key}>
                    {farm.name}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
          <FormControl className={styles.filterFormControl} size="small">
            <Select
              displayEmpty
              value={formik.values.pond_id}
              onChange={(e) => onFilterChange("pond_id", e.target.value)}
              className={styles.filterSelectOption}
            >
              <MenuItem disabled value="">
                <em>{t("POND")}</em>
              </MenuItem>
              {ponds &&
                ponds.map((pond, key) => (
                  <MenuItem value={pond.id} key={key}>
                    {pond.name}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
          <FormControl className={styles.filterFormControl} size="small">
            <Select
              value={formik.values.cycle_id}
              onChange={(event) =>
                onFilterChange(
                  "cycle_id",
                  typeof event.target.value === "string"
                    ? event.target.value.split(",")
                    : event.target.value
                )
              }
              input={<OutlinedInput label="Cycle" />}
              className={styles.filterSelectOption}
              renderValue={(selected) => {
                if (selected.length === 0) {
                  return <em>{t("CYCLE")}</em>;
                }
                return cycles
                  .filter((cycle) => selected.includes(cycle.id))
                  .map((cycle) => cycle.name)
                  .join(", ");
              }}
              multiple
              displayEmpty
            >
              <MenuItem disabled value="">
                <em>{t("CYCLE")}</em>
              </MenuItem>
              {cycles &&
                cycles.map((cycle, key) => (
                  <MenuItem value={cycle.id} key={key}>
                    {cycle.name}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
          <StartDatePickerPopUp formik={formik} daterange={daterange} />
          <EndDatePickerPopUp formik={formik} daterange={daterange} />
          <FormControl className={styles.filterFormControl} size="small">
            <Select
              value={formik.values.variables}
              onChange={(event) =>
                onFilterChange(
                  "variables",
                  typeof event.target.value === "string"
                    ? event.target.value.split(",")
                    : event.target.value
                )
              }
              input={<OutlinedInput label={t("MENU.WATER_QUALITY")} />}
              className={styles.filterSelectOption}
              renderValue={(selected) => {
                if (selected.length === 0) {
                  return <em>{t("MENU.WATER_QUALITY")}</em>;
                }
                return variables
                  .filter((variable) => selected.includes(variable))
                  .map((variable) => variable)
                  .join(", ");
              }}
              multiple
              displayEmpty
            >
              <MenuItem disabled value="">
                <em>{t("MENU.WATER_QUALITY")}</em>
              </MenuItem>
              {variables &&
                variables.map((variable, key) => (
                  <MenuItem value={variable} key={key}>
                    {variable}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
          <Button
            disabled={!formik.dirty || Object.keys(formik.errors).length > 0}
            type="submit"
            classes={{
              disabled: styles.filterButtonDisabled,
            }}
            className={styles.filterButton}
          >
            {t("APPLY_FILTER")}
          </Button>
          <Button
            onClick={formik.handleReset}
            type="reset"
            className={styles.filterButton}
          >
            {t("RESET_FILTER")}
          </Button>
        </div>
      </form>
    </Fragment>
  );
};

export default Filter;
