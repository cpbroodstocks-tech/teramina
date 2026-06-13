import { useStyles } from "components/footer/styles";
import { Button, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

const Footer = () => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();

  return (
    <footer className={styles.footer}>
      <Typography className={styles.copyright}>
        {t("BROUGHT_TO_YOU_BY_TERAMINA")}
      </Typography>
      <Stack direction="row" spacing={1} sx={{ justifyContent: "center" }}>
        <Button component={Link} to="/services" color="inherit">Services</Button>
        <Button component={Link} to="/knowledge" color="inherit">Knowledge</Button>
      </Stack>
      {/* <img
        className={styles.lgFooter}
        src="/assets/images/lgFooter.svg"
        alt="mui logo"
      /> */}
    </footer>
  );
};

export default Footer;
