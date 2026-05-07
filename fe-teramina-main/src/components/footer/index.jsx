import { useStyles } from "components/footer/styles";
import { Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

const Footer = () => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();

  return (
    <footer className={styles.footer}>
      <Typography className={styles.copyright}>
        {t("BROUGHT_TO_YOU_BY_TERAMINA")}
      </Typography>
      {/* <img
        className={styles.lgFooter}
        src="/assets/images/lgFooter.svg"
        alt="mui logo"
      /> */}
    </footer>
  );
};

export default Footer;
