import React, { useState } from "react";
import Footer from "components/footer";
import { useStyles } from "pages/signup/styles";
import { Typography, Avatar, Box, Button } from "@mui/material";
import { Navigate } from "react-router-dom";
import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";
import { useLocalStorage } from "hooks/useLocalStorage";
import Error from "components/error";

const SignUp = () => {
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
        <div className={styles.contentSignUp}>
          <div className={styles.leftContent}>
            <Box className={styles.formWrapper}>
              <Typography
                variant="h2"
                component="h2"
                className={styles.headingSignUp}
              >
                Create your account
              </Typography>
              <Button
                onClick={handleOnClick}
                variant="outlined"
                className={styles.btnSignUp}
                startIcon={
                  <Avatar
                    src="/assets/images/lgGoogle.png"
                    className={styles.avatarGoogle}
                  />
                }
              >
                Sign up with Google
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

export default SignUp;
