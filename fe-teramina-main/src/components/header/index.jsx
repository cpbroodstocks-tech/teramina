import { useState, useEffect } from "react";
import { useStyles } from "components/header/styles";
import { GiHamburgerMenu } from "react-icons/gi";
import { Button, Tooltip, Badge, IconButton } from "@mui/material";
import { getAuth, signOut } from "firebase/auth";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Typography from "@mui/material/Typography";
import { useUserStore } from "store/user.store";
import { useNavigate } from "react-router-dom";
import Language from "components/language";
import { useTranslation } from "react-i18next";
import { RiRobot2Line } from "react-icons/ri";
import AgentChat from "components/agent-chat";

const Header = (props) => {
  const { t } = useTranslation();
  const { open, setOpen } = props;
  const [anchorElUser, setAnchorElUser] = useState(() => null);
  const [agentOpen, setAgentOpen] = useState(false);
  const [alertCount, setAlertCount] = useState(0);
  const [pendingMessage, setPendingMessage] = useState("");
  const { user } = useUserStore();
  const { classes: styles } = useStyles();
  const navigate = useNavigate();

  useEffect(() => {
    const handler = (e) => {
      if (e.detail?.message) setPendingMessage(e.detail.message);
      setAgentOpen(true);
    };
    window.addEventListener("open-agent-chat", handler);
    return () => window.removeEventListener("open-agent-chat", handler);
  }, []);

  const handleOpenUserMenu = (event) => {
    setAnchorElUser(event.currentTarget);
  };

  const handleCloseUserMenu = () => {
    setAnchorElUser(null);
  };

  const handleLogout = () => {
    const auth = getAuth();
    signOut(auth).then(() => navigate("/signin"));
  };

  const displayName = user && user.name && user.name.split(" ");

  return (
    <header className={styles.header}>
      <Button onClick={() => setOpen(!open)} className={styles.toggleButton}>
        <GiHamburgerMenu />
        {/* Buka Menu */}
      </Button>

      {user && (
        <>
          <Tooltip title="AI Assistant">
            <IconButton onClick={() => setAgentOpen(true)}>
              <Badge badgeContent={alertCount} color="error">
                <RiRobot2Line />
              </Badge>
            </IconButton>
          </Tooltip>
          <AgentChat
            open={agentOpen}
            onClose={() => setAgentOpen(false)}
            onAlertsLoaded={setAlertCount}
            initialMessage={pendingMessage}
            onInitialMessageConsumed={() => setPendingMessage("")}
          />
          <Tooltip title={t("OPEN_SETTINGS")}>
            <Button className={styles.userButton} onClick={handleOpenUserMenu}>
              <div className={styles.avatarContainer}>
                {user.picture ? (
                  <img
                    src={user?.picture}
                    className={styles.avatarUser}
                    referrerPolicy="no-referrer"
                    rel="noreferrer"
                    alt="profile"
                  />
                ) : (
                  <img
                    src="/assets/images/no-profile-picture.jpg"
                    alt="profile"
                    className={styles.avatarUser}
                  />
                )}
              </div>
              {/* in order to limit name */}
              {displayName && displayName[0] ? displayName[0] : null}{" "}
              {displayName && displayName[1] ? displayName[1] : null}
            </Button>
          </Tooltip>
          <Menu
            className={styles.menuHeader}
            anchorEl={anchorElUser}
            anchorOrigin={{
              vertical: "bottom",
              horizontal: "right",
            }}
            transformOrigin={{
              vertical: "top",
              horizontal: "right",
            }}
            open={Boolean(anchorElUser)}
            onClose={handleCloseUserMenu}
          >
            <MenuItem key="profile" onClick={() => { handleCloseUserMenu(); navigate("/dashboard/profile"); }}>
              <Typography textAlign="center" className={styles.labelMenu}>
                {t("MENU.PROFILE")}
              </Typography>
            </MenuItem>
            <MenuItem key="logout" onClick={handleLogout}>
              <Typography textAlign="center" className={styles.labelMenu}>
                {t("LOGOUT")}
              </Typography>
            </MenuItem>
          </Menu>
        </>
      )}

      <Language />
    </header>
  );
};

export default Header;
