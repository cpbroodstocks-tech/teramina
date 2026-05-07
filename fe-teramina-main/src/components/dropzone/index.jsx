import { Fragment, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Typography } from "@mui/material";
import { BsCloudUpload } from "react-icons/bs";
import { useStyles } from "components/dropzone/styles";
import { useTranslation } from "react-i18next";

const TeraminaDropzone = ({
  changeFile = () => {},
  message = "Supported format: .csv, .xlsx",
  multiple = false,
  accept = {
    "text/csv": [".csv"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
      ".xlsx",
    ],
  },
}) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();

  const onDrop = useCallback((acceptedFiles) => {
    changeFile(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, acceptedFiles } = useDropzone({
    onDrop,
    multiple: multiple,
    accept: accept,
  });

  return (
    <Fragment>
      <div
        {...getRootProps({
          className: styles.dropzone,
        })}
      >
        <input {...getInputProps()} name="hai" />
        {acceptedFiles.length === 0 && (
          <Fragment>
            <BsCloudUpload className={styles.uploadIcon} />
            <Typography variant="p" className={styles.description}>
              {t("DRAG_DROP_FILES_OR")}
              <span>&nbsp;{t("BROWSE")}</span>
            </Typography>
            <Typography variant="p" className={styles.subDescription}>
              {message}
            </Typography>
          </Fragment>
        )}
        {acceptedFiles.length > 0 && (
          <Fragment>
            <Typography className={styles.description}>
              {acceptedFiles[0].name}
            </Typography>
          </Fragment>
        )}
      </div>
    </Fragment>
  );
};

export default TeraminaDropzone;
