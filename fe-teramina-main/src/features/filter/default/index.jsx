import { Fragment } from "react";
import { MenuItem, FormControl, Select, Button } from "@mui/material";
import DatePickerPopUp from "features/filter/default/components/datepicker-popup";
import { useStyles } from "features/filter/default/styles";
import { useTranslation } from "react-i18next";

const Filter = ({ filter, form, onFilterChange }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { farms, ponds, cycles, daterange } = filter;

  return (
    <Fragment>
      <form onSubmit={form.handleSubmit}>
        <div className={styles.filterWrapper}>
          <FormControl className={styles.filterFormControl} size="small">
            <Select
              displayEmpty
              name="farm_id"
              defaultValue={""}
              value={form.values.farm_id}
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
              value={form.values.pond_id}
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
              value={form.values.cycle_id}
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
          <DatePickerPopUp form={form} daterange={daterange} />
          <Button
            disabled={!form.dirty || Object.keys(form.errors || {}).length > 0}
            type="submit"
            classes={{
              disabled: styles.filterButtonDisabled,
            }}
            className={styles.filterButton}
          >
            {t("APPLY_FILTER")}
          </Button>
          <Button
            onClick={form.handleReset}
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
