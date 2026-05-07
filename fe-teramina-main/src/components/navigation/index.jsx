import React from "react";
import { useStyles } from "components/navigation/styles";
import Button from "@mui/material/Button";
import { useTranslation } from "react-i18next";

const Navigation = () => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  return (
    <div className={styles.navigation}>
      <Button variant="text" sx={{ fontSize: 24, color: "#000" }}>
        {t("HOME")}
      </Button>
      <Button
        variant="contained"
        sx={{ fontSize: 24, margin: "0 80px" }}
        color="primary"
      >
        {t("GET_STARTED")}
      </Button>
      <Button variant="text" sx={{ fontSize: 24, color: "#000" }}>
        {t("LOGIN")}
      </Button>
    </div>
  );
};

export default Navigation;
