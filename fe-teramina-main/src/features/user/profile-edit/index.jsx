import { Fragment, useEffect } from "react";
import { Typography, TextField, Button, CircularProgress } from "@mui/material";
import classNames from "classnames";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useStyles } from "./styles";
import Error from "components/error";
import TeraminaDropzone from "components/dropzone";
import { useUserStore } from "store/user.store";
import { useToastStore } from "store/toast.store";
import { useTranslation } from "react-i18next";
import { useUserProfile, useUpdateProfile } from "features/user/queries";

const regexPhone = /^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[0-9]{8,16}$/;

const ProfileEdit = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { setUser } = useUserStore();
  const { setToast: toast } = useToastStore();
  const { classes: styles } = useStyles();

  const schema = z.object({
    name: z.string().min(1, t("FIELD_REQUIRED_MESSAGE")),
    phone: z.string().min(1, t("FIELD_REQUIRED_MESSAGE")).regex(regexPhone, t("PHONE_NUMBER_WRONG_MESSAGE")),
    address: z.string().min(1, t("FIELD_REQUIRED_MESSAGE")),
    file: z.any().optional(),
  });

  const { register, handleSubmit, reset, setValue, formState } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { name: "", phone: "", address: "", file: [] },
  });

  const { data: profile, isError } = useUserProfile();
  const { mutateAsync: updateProfile } = useUpdateProfile();

  useEffect(() => {
    if (profile) {
      reset({ name: profile.name ?? "", phone: profile.phone ?? "", address: profile.address ?? "", file: [] });
    }
  }, [profile]);

  const onSubmit = async (values) => {
    try {
      const formData = new FormData();
      formData.append("name", values.name);
      formData.append("phone", values.phone);
      formData.append("address", values.address);
      if (values.file && values.file[0]) formData.append("file", values.file[0]);

      const updated = await updateProfile(formData);
      setUser(updated);
      toast({ open: true, variant: "success", text: t("EDIT_PROFILE_SUCCESS_MESSAGE") });
      setTimeout(() => { navigate("/dashboard/profile"); }, 1000);
    } catch {
      toast({ open: true, variant: "error", text: t("EDIT_PROFILE_FAILED_MESSAGE") });
    }
  };

  if (isError) return <Error />;

  const changeFile = (newValue) => setValue("file", newValue);

  return (
    <Fragment>
      <form className={styles.container} onSubmit={handleSubmit(onSubmit)}>
        <div className={styles.column}>
          <Typography variant="h5" className={styles.title}>{t("COMPLETE_YOUR_PROFILE")}</Typography>
          <Typography variant="h6" className={classNames(styles.label, styles.requiredLabel)}>{t("YOUR_NAME")}</Typography>
          <TextField
            variant="outlined"
            className={styles.input}
            error={!!formState.errors.name}
            helperText={formState.errors.name?.message}
            {...register("name")}
          />
          <Typography variant="h6" className={classNames(styles.label, styles.requiredLabel)}>{t("YOUR_PHONE_NUMBER")}</Typography>
          <TextField
            variant="outlined"
            className={styles.input}
            error={!!formState.errors.phone}
            helperText={formState.errors.phone?.message}
            {...register("phone")}
          />
          <Typography variant="h6" className={classNames(styles.label, styles.requiredLabel)}>{t("YOUR_ADDRESS")}</Typography>
          <TextField
            variant="outlined"
            className={styles.input}
            error={!!formState.errors.address}
            helperText={formState.errors.address?.message}
            {...register("address")}
          />
          <Button
            type="submit"
            variant="contained"
            className={styles.btnSubmit}
            disabled={formState.isSubmitting}
          >
            {formState.isSubmitting ? (
              <CircularProgress color="inherit" classes={{ root: styles.circular }} />
            ) : t("SUBMIT")}
          </Button>
        </div>
        <div className={styles.column}>
          <Typography variant="h5" className={styles.title}>{t("UPLOAD_PROFILE_PHOTO")}</Typography>
          <TeraminaDropzone
            changeFile={changeFile}
            message={t("SUPPORTED_FORMAT_IMAGE")}
            multiple={false}
            accept={{
              "image/jpg": [".jpg"],
              "image/jpeg": [".jpeg"],
              "image/png": [".png"],
              "image/img": [".img"],
            }}
          />
        </div>
      </form>
    </Fragment>
  );
};

export default ProfileEdit;
