import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import { Popover, TextField, Typography } from "@mui/material";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { StaticDatePicker } from "@mui/x-date-pickers/StaticDatePicker";
import { useStyles } from "features/filter/default/components/datepicker-popup/styles";
import dayjs from "dayjs";
import { Fragment, useState } from "react";
import { useTranslation } from "react-i18next";

const DatePickerPopUp = ({ formik, daterange }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const [anchorEl, setAnchorEl] = useState(() => null);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleChangePicker = (newDate) => {
    const date = dayjs(newDate).format("MM/DD/YYYY");
    formik.setFieldValue("date", date);
    handleClose();
  };

  const open = Boolean(anchorEl);
  const id = open ? "datepicker-popover" : undefined;

  return (
    <Fragment>
      {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/interactive-supports-focus */}
      <div
        aria-describedby={id}
        role="button"
        onClick={handleClick}
        className={styles.button}
      >
        <Typography variant="h6">
          {formik.values.date ? formik.values.date : t("DATE")}
        </Typography>
        <ArrowDropDownIcon className={styles.buttonIcon} />
      </div>
      <Popover
        id={id}
        open={open}
        anchorEl={anchorEl}
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
        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <StaticDatePicker
            displayStaticWrapperAs="desktop"
            openTo="day"
            inputFormat="MM/DD/YYYY"
            minDate={daterange.start_date ? dayjs(daterange.start_date) : undefined}
            maxDate={daterange.end_date ? dayjs(daterange.end_date) : undefined}
            onChange={(newDate) => {
              handleChangePicker(newDate);
            }}
            className={styles.calendar}
            value={formik.values.date ? dayjs(formik.values.date) : null}
            renderInput={(params) => <TextField {...params} />}
          />
        </LocalizationProvider>
      </Popover>
    </Fragment>
  );
};

export default DatePickerPopUp;
