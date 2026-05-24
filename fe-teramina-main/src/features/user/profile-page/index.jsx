import { Fragment } from "react";
import { useNavigate } from "react-router-dom";
import { Card, Typography, Button } from "@mui/material";
import { useStyles } from "./styles";
import Error from "components/error";
import { useTranslation } from "react-i18next";
import { useUserProfile } from "features/user/queries";

const Profile = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { classes: styles } = useStyles();
  const { data: user, isError } = useUserProfile();

  if (isError) return <Error />;

  return (
    <Fragment>
      <Typography variant="h5" className={styles.titlePage}>
        {t("MENU.PROFILE")}
      </Typography>
      <div className={styles.container}>
        <div className={styles.wrapProfileFoto}>
          <div className={styles.containerProfileFoto}>
            {user?.picture ? (
              <img src={user.picture} alt="profile" className={styles.imgProfileFoto} />
            ) : (
              <img src="/assets/images/no-profile-picture.jpg" alt="profile" className={styles.imgProfileFoto} />
            )}
          </div>
          <div className={styles.wrapUsername}>
            <Typography variant="h1" className={styles.textUsername}>
              {user?.name ?? "-"}
            </Typography>
            <Button
              variant="contained"
              className={styles.btnEditProfile}
              onClick={() => navigate("/dashboard/profile/edit")}
            >
              {t("EDIT_PROFILE")}
            </Button>
          </div>
        </div>

        <Card className={styles.infoCard}>
          <Typography className={styles.titleField} variant="body1">{t("PHONE_NUMBER")}</Typography>
          <Typography className={styles.valueField} variant="h4"><span>{user?.phone ?? "-"}</span></Typography>
        </Card>
        <Card className={styles.infoCard}>
          <Typography className={styles.titleField} variant="body1">{t("EMAIL")}</Typography>
          <Typography className={styles.valueField} variant="h4"><span>{user?.email ?? "-"}</span></Typography>
        </Card>
        <Card className={styles.infoCard}>
          <Typography className={styles.titleField} variant="body1">{t("ADDRESS")}</Typography>
          <Typography className={styles.valueField} variant="h4"><span>{user?.address ?? "-"}</span></Typography>
        </Card>
      </div>
    </Fragment>
  );
};

export default Profile;
