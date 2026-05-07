import {
  Button,
  Menu,
  MenuItem,
  Typography,
  useMediaQuery,
} from "@mui/material";
import { useStyles } from "components/language/styles";
import { useLanguage } from "hooks/useLanguage";
import { useState } from "react";
import { FaGlobe } from "react-icons/fa";
import { useLocation } from "react-router-dom";
import { theme } from "theme";

const Language = () => {
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const { pathname } = useLocation();
  const isDashboard = pathname.includes("dashboard");
  const propStyles = {
    isDashboard,
  };
  const styles = useStyles(propStyles);
  const { getLang, setLang } = useLanguage();
  const getCurrentLang = getLang("lang") === "en" ? "EN" : "ID";
  const [currentLanguage, setCurrentLanguage] = useState(getCurrentLang);
  const [anchorElLanguage, setAnchorElLanguage] = useState(() => null);
  const languageMenu = [
    {
      key: "en",
      icon: (
        <img
          alt="english"
          src="/assets/images/english.png"
          width={30}
        />
      ),
      label: "English",
    },
    {
      key: "id",
      icon: (
        <img
          alt="indonesia"
          src="/assets/images/indonesia.png"
          width={30}
        />
      ),
      label: "Indonesia",
    },
  ];

  const selectLanguage = (type) => () => {
    switch (type) {
    case "en":
      setLang("en");
      setCurrentLanguage("EN");
      break;
    case "id":
      setLang("id");
      setCurrentLanguage("ID");
      break;
    }
    handleCloseLanguage();
  };

  const handleOpenLanguage = (e) => {
    setAnchorElLanguage(e.currentTarget);
  };
  const handleCloseLanguage = () => setAnchorElLanguage(null);
  return (
    <>
      <Button
        variant="text"
        className={styles.btnLanguage}
        onClick={handleOpenLanguage}
      >
        {isMobile ? null : <FaGlobe size={35} />}
        <Typography className={styles.textLanguage}>
          {currentLanguage}
        </Typography>
      </Button>
      <Menu
        className={styles.menuLanguage}
        anchorEl={anchorElLanguage}
        transformOrigin={{ horizontal: "right", vertical: "top" }}
        anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
        open={Boolean(anchorElLanguage)}
        onClose={handleCloseLanguage}
      >
        {languageMenu.map((lang) => {
          return (
            <MenuItem
              key={lang.key}
              className={styles.menuItemLanguage}
              onClick={selectLanguage(lang.key)}
            >
              {lang.icon}
              <Typography className={styles.labelLanguage}>
                {lang.label}
              </Typography>
            </MenuItem>
          );
        })}
      </Menu>
    </>
  );
};

export default Language;
