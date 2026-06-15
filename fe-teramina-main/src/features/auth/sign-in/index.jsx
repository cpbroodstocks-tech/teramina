import { useState } from "react";
import Footer from "components/footer";
import { useStyles } from "./styles";
import { Alert, Typography, Avatar, Box, Button, CircularProgress } from "@mui/material";
import { Navigate } from "react-router-dom";
import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";
import { useLocalStorage } from "hooks/useLocalStorage";
import Error from "components/error";
import { useTranslation } from "react-i18next";

const SignIn = () => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { get } = useLocalStorage();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const isAuthenticated = get("authentication");
  if (isAuthenticated) return <Navigate to={"/dashboard"} />;

  const handleOnClick = async () => {
    const auth = getAuth();
    const provider = new GoogleAuthProvider();
    setError(null);
    setLoading(true);
    try {
      const response = await signInWithPopup(auth, provider);
      if (!response) throw response;
    } catch (err) {
      const recoverableErrors = {
        "auth/popup-closed-by-user": "SIGN_IN_POPUP_CLOSED",
        "auth/cancelled-popup-request": "SIGN_IN_POPUP_CLOSED",
        "auth/popup-blocked": "SIGN_IN_POPUP_BLOCKED",
        "auth/network-request-failed": "SIGN_IN_NETWORK_ERROR",
      };
      setError(recoverableErrors[err?.code] || "ACCESS_DENIED");
    } finally {
      setLoading(false);
    }
  };

  if (error === "ACCESS_DENIED") {
    return (
      <Error
        title={t("ACCESS_NOT_ENABLED")}
        message={t("CLOSED_BETA_MESSAGE")}
        actionLabel={t("REQUEST_ACCESS")}
        onAction={() => { window.location.href = "/#waitlist"; }}
        secondaryLabel={t("TRY_ANOTHER_ACCOUNT")}
        onSecondary={() => setError(null)}
      />
    );
  }

  return (
    <>
      <div>
        <div className={styles.headerLogo}>
          <img src="/assets/images/logo-teramina.png" alt="logo" />
        </div>
        <div className={styles.contentSignIn}>
          <div className={styles.leftContent}>
            <Box className={styles.formWrapper}>
              <Typography
                variant="span"
                component="span"
                className={styles.headingSmallSignIn}
              >
                {t("WELCOME_BACK")} 👋
              </Typography>
              <Typography
                variant="h2"
                component="h2"
                className={styles.headingSignIn}
              >
                {t("SIGN_IN_TO_YOUR_ACCOUNT")}
              </Typography>
              <Button
                onClick={handleOnClick}
                variant="outlined"
                className={styles.btnSignIn}
                disabled={loading}
                startIcon={
                  loading
                    ? <CircularProgress size={20} />
                    : <Avatar src="/assets/images/lgGoogle.png" className={styles.avatarGoogle} alt="" />
                }
              >
                {loading ? t("SIGNING_IN") : t("LOGIN_WITH_GOOGLE")}
              </Button>
              {error && <Alert severity="error" sx={{ mt: 2 }}>{t(error)}</Alert>}
            </Box>
          </div>
          <div className={styles.rightContent}>
            <div className={styles.overlay}></div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
};

export default SignIn;
