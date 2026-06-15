import { FormControl, InputLabel, MenuItem, OutlinedInput, Select } from "@mui/material";
import PageFilterBar from "components/page-filter-bar";
import {
  EndDatePickerPopUp,
  StartDatePickerPopUp,
} from "features/filter/water-quality/components/datepicker-popup";
import { useTranslation } from "react-i18next";

const Filter = ({ filter, form, onFilterChange }) => {
  const { t } = useTranslation();
  const variables = filter.variables || [];

  return (
    <form onSubmit={form.handleSubmit}>
      <PageFilterBar
        dirty={form.dirty}
        disabled={Object.keys(form.errors || {}).length > 0}
        onReset={form.handleReset}
      >
        <StartDatePickerPopUp form={form} daterange={filter.daterange} />
        <EndDatePickerPopUp form={form} daterange={filter.daterange} />
        <FormControl size="small" sx={{ minWidth: 220 }}>
          <InputLabel id="water-quality-variables-label">{t("WATER_QUALITY_VARIABLES")}</InputLabel>
          <Select
            labelId="water-quality-variables-label"
            value={form.values.variables}
            onChange={(event) => onFilterChange(
              "variables",
              typeof event.target.value === "string" ? event.target.value.split(",") : event.target.value
            )}
            input={<OutlinedInput label={t("WATER_QUALITY_VARIABLES")} />}
            renderValue={(selected) => selected.length
              ? selected.join(", ")
              : <em>{t("WATER_QUALITY_VARIABLES")}</em>}
            multiple
            displayEmpty
          >
            {variables.map((variable) => <MenuItem value={variable} key={variable}>{variable}</MenuItem>)}
          </Select>
        </FormControl>
      </PageFilterBar>
    </form>
  );
};

export default Filter;
