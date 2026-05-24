import React, { useState } from "react";
import Footer from "components/footer";
import { useStyles } from "./styles";
import { Typography, Avatar, Box, Button } from "@mui/material";
import { Navigate } from "react-router-dom";
import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";
import { useLocalStorage } from "hooks/useLocalStorage";
import Error from "components/error";
import { useTranslation } from "react-i18next";

const SignIn = () => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { get } = useLocalStorage();
  const [error, setError] = useState(false);

  const isAuthenticated = get("authentication");
  if (isAuthenticated) return <Navigate to={"/dashboard"} />;

  const handleOnClick = async () => {
    const auth = getAuth();
    const provider = new GoogleAuthProvider();
    try {
      const response = await signInWithPopup(auth, provider);
      if (!response) throw response;
    } catch (err) {
      setError(true);
    }
  };

  if (error) return <Error />;

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
                startIcon={
                  <Avatar
                    src="/assets/images/lgGoogle.png"
                    className={styles.avatarGoogle}
                  />
                }
              >
                {t("LOGIN_WITH_GOOGLE")}
              </Button>
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
