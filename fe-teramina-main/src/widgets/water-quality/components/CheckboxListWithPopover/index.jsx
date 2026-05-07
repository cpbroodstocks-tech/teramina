import React, { useState } from "react";
import { useStyles } from "./styles";
import {
  Card,
  Checkbox,
  Typography,
  Popover,
} from "@mui/material";

const CheckboxListWithPopover = ({ checkboxes, checkedItems, handleCheckboxChange }) => {
  const { classes } = useStyles();
  const [anchorEl, setAnchorEl] = useState(null);

  const handlePopoverOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handlePopoverClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

  return (
    <div>
      <Card
        className={classes.cardCheckboxContainer}
        onClick={handlePopoverOpen}
      >
        {checkboxes.map((item) => (
          <div key={item} className={classes.checkbox}>
            <Checkbox
              checked={checkedItems[item] || false}
              onChange={() => handleCheckboxChange(item)}
            />
            <Typography>{item}</Typography>
          </div>
        ))}
      </Card>
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handlePopoverClose}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "left",
        }}
      >
        <div className={classes.popoverContent}>
          <div className={classes.columns}>
            <div className={classes.column}>
              {checkboxes
                .slice(0, Math.ceil(checkboxes.length / 3))
                .map((item) => (
                  <div key={item} className={classes.checkbox}>
                    <Checkbox
                      checked={checkedItems[item] || false}
                      onChange={() => handleCheckboxChange(item)}
                    />
                    <Typography>{item}</Typography>
                  </div>
                ))}
            </div>
            <div className={classes.column}>
              {checkboxes
                .slice(
                  Math.ceil(checkboxes.length / 3),
                  Math.ceil((2 * checkboxes.length) / 3)
                )
                .map((item) => (
                  <div key={item} className={classes.checkbox}>
                    <Checkbox
                      checked={checkedItems[item] || false}
                      onChange={() => handleCheckboxChange(item)}
                    />
                    <Typography>{item}</Typography>
                  </div>
                ))}
            </div>
            <div className={classes.column}>
              {checkboxes
                .slice(Math.ceil((2 * checkboxes.length) / 3))
                .map((item) => (
                  <div key={item} className={classes.checkbox}>
                    <Checkbox
                      checked={checkedItems[item] || false}
                      onChange={() => handleCheckboxChange(item)}
                    />
                    <Typography>{item}</Typography>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </Popover>
    </div>
  );
};

export { CheckboxListWithPopover };
