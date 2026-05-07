import { Fragment } from "react";
import { MenuItem, FormControl, Select, Button } from "@mui/material";
import DatePickerPopUp from "features/filter/default/components/datepicker-popup";
import { useStyles } from "features/filter/default/styles";
import { useTranslation } from "react-i18next";

const Filter = ({ filter, formik, onFilterChange }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { farms, ponds, cycles, daterange } = filter;

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
              displayEmpty
              value={formik.values.cycle_id}
              onChange={(e) => onFilterChange("cycle_id", e.target.value)}
              className={styles.filterSelectOption}
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
          <DatePickerPopUp formik={formik} daterange={daterange} />
          <Button
            disabled={!formik.dirty}
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
