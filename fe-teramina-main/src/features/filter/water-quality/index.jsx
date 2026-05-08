import { Fragment, useState } from "react";
import { ReactSVG } from "react-svg";
import {
  IconButton,
  Paper,
  ToggleButtonGroup,
  ToggleButton,
  MenuItem,
  FormControl,
  Select,
  Button,
  Checkbox,
  Typography,
  Popover,
} from "@mui/material";
import DatePickerPopUp from "features/filter/kualitas-air/components/datepicker-popup";
import { useStyles } from "features/filter/kualitas-air/styles";

import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import siklusList from "pages/dashboard/kualitas_air/dummy/cyclecheckbox.json";
import kualitasAirList from "pages/dashboard/kualitas_air/dummy/kualitasaircheckbox.json";

import iconChartActive from "/assets/images/icons/chartactive.svg";
import iconPlotNotActive from "/assets/images/icons/plotnotactive.svg";

import ViewComfyOutlinedIcon from "@mui/icons-material/ViewComfyOutlined";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import { useTranslation } from "react-i18next";

const FilterKualitasAir = ({ filter, form, onFilterChange }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { farms, ponds, cycles, daterange } = filter;

  const dataKualitasAir = kualitasAirList.data;
  const dataSiklus = siklusList.data;

  const [checkedItemsSiklus, setCheckedItemsSiklus] = useState([]);
  const [checkedItemsKualitasAir, setCheckedItemsKualitasAir] = useState([]);
  const [anchorElKualitasAir, setAnchorElKualitasAir] = useState(null);
  const [anchorElSiklus, setAnchorElSiklus] = useState(null);

  const handleClickSiklus = (event) => {
    setAnchorElSiklus(event.currentTarget);
  };

  const handleClickKualitasAir = (event) => {
    setAnchorElKualitasAir(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorElSiklus(null);
    setAnchorElKualitasAir(null);
  };

  const handleCheckboxSiklusChange = (item) => {
    setCheckedItemsSiklus((prevCheckedItems) => {
      const isChecked = prevCheckedItems.some(
        (checkedItem) => checkedItem.value === item.value
      );
      if (isChecked) {
        return prevCheckedItems.filter(
          (checkedItem) => checkedItem.value !== item.value
        );
      } else {
        return [...prevCheckedItems, { label: item.label, value: item.value }];
      }
    });
  };

  const handleCheckboxKualitasAirChange = (item) => {
    setCheckedItemsKualitasAir((prevCheckedItems) => {
      const isChecked = prevCheckedItems.some(
        (checkedItem) => checkedItem.value === item.value
      );
      if (isChecked) {
        return prevCheckedItems.filter(
          (checkedItem) => checkedItem.value !== item.value
        );
      } else {
        return [...prevCheckedItems, { label: item.label, value: item.value }];
      }
    });
  };

  return (
    <Fragment>
      <form
        onSubmit={form.handleSubmit}
        className={styles.wrapperToolbarFilter}
      >
        <div className={styles.filterWrapper}>
          <FormControl className={styles.filterFormControl} size="small">
            <Select
              displayEmpty
              name="farm_id"
              defaultValue={""}
              variant="outlined"
              value={form.values.farm_id}
              onChange={(e) => onFilterChange("farm_id", e.target.value)}
              className={styles.filterSelectOption}
              classes={{ select: styles.filterSelectOptionCustom }}
              IconComponent={() => <KeyboardArrowDownIcon />}
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
              classes={{ select: styles.filterSelectOptionCustom }}
              endAdornment={
                <IconButton edge="end" color="inherit" aria-label="arrow">
                  <KeyboardArrowDownIcon />
                </IconButton>
              }
              IconComponent={() => null}
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
            <Button
              className={styles.filterButton}
              onClick={handleClickSiklus}
              variant="outlined"
              endIcon={<KeyboardArrowDownIcon />}
            >
              {t("CYCLE")}
            </Button>
            <Popover
              open={Boolean(anchorElSiklus)}
              anchorEl={anchorElSiklus}
              onClose={handleClose}
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "center",
              }}
              transformOrigin={{
                vertical: "top",
                horizontal: "center",
              }}
              className={styles.popoverSiklus}
            >
              <div className={styles.containerPoppoverSiklus}>
                {dataSiklus.map((item) => (
                  <div key={item.value} className={styles.itemSiklus}>
                    <Checkbox
                      checked={checkedItemsSiklus.some(
                        (checkedItem) => checkedItem.value === item.value
                      )}
                      onChange={() => handleCheckboxSiklusChange(item)}
                      className={styles.roundCheckbox}
                      classes={{
                        root: styles.roundCheckboxCustom,
                      }}
                      icon={<RadioButtonUncheckedIcon />}
                      checkedIcon={<CheckCircleOutlineIcon color="green" />}
                    />

                    <Typography>{item.label}</Typography>
                  </div>
                ))}
              </div>
            </Popover>
          </FormControl>
          <DatePickerPopUp form={form} daterange={daterange} />
          <FormControl className={styles.filterFormControl} size="small">
            <Select
              displayEmpty
              className={styles.filterSelectOption}
              classes={{ select: styles.filterSelectOptionCustom }}
              value={""}
              endAdornment={
                <IconButton edge="end" color="inherit" aria-label="arrow">
                  <KeyboardArrowDownIcon />
                </IconButton>
              }
              IconComponent={() => null}
            >
              <MenuItem disabled value="">
                <em>DOC</em>
              </MenuItem>
              {cycles &&
                cycles.map((cycle, key) => (
                  <MenuItem value={cycle.id} key={key}>
                    {cycle.name}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
          <FormControl className={styles.filterFormControl} size="small">
            <Button
              className={styles.filterButton}
              onClick={handleClickKualitasAir}
              variant="outlined"
              endIcon={<KeyboardArrowDownIcon />}
            >
              {t("MENU.WATER_QUALITY")}
            </Button>
            <Popover
              open={Boolean(anchorElKualitasAir)}
              anchorEl={anchorElKualitasAir}
              onClose={handleClose}
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "center",
              }}
              transformOrigin={{
                vertical: "top",
                horizontal: "center",
              }}
            >
              <div className={styles.containerPoppoverKualitasAir}>
                {dataKualitasAir.map((item) => (
                  <div key={item.value} className={styles.itemKualitasAir}>
                    <Checkbox
                      checked={checkedItemsKualitasAir.some(
                        (checkedItem) => checkedItem.value === item.value
                      )}
                      onChange={() => handleCheckboxKualitasAirChange(item)}
                      className={styles.roundCheckbox}
                      classes={{
                        root: styles.roundCheckboxCustom,
                      }}
                      icon={<RadioButtonUncheckedIcon />}
                      checkedIcon={<CheckCircleOutlineIcon color="green" />}
                    />

                    <Typography>{item.label}</Typography>
                  </div>
                ))}
              </div>
            </Popover>
          </FormControl>
        </div>

        <Paper className={styles.typeChartWrapper}>
          <ToggleButtonGroup
            orientation="horizontal"
            exclusive
            value="chart"
            className={styles.groupedTypeCart}
          >
            <ToggleButton value="chart" className={styles.typeChartButton}>
              <ReactSVG src={iconChartActive} />
            </ToggleButton>
            <ToggleButton value="plot" className={styles.typeChartButton}>
              <ReactSVG src={iconPlotNotActive} />
            </ToggleButton>
            <ToggleButton value="table" className={styles.typeChartButton}>
              {/* <ReactSVG src={iconTableActive} /> */}
              <ViewComfyOutlinedIcon sx={{ fontSize: 30, color: "#9E9E9E" }} />
            </ToggleButton>
          </ToggleButtonGroup>
        </Paper>
      </form>
    </Fragment>
  );
};

export default FilterKualitasAir;
