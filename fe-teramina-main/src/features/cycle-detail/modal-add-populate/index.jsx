import { Fragment, useState } from "react";
import { Button, Box, CircularProgress, Dialog, DialogContent, Typography } from "@mui/material";
import { useToastStore } from "store/toast.store";
import { useStyles } from "features/cycle-detail/modal-add-populate/styles";
import { usePopulateCycleData, useDownloadDummyData } from "features/cycle-detail/queries";
import { useParams } from "react-router-dom";
import TeraminaDropzone from "components/dropzone";
import { useModal } from "hooks/useModal";
import { useTranslation } from "react-i18next";

const PopulateAdd = ({ onClose }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { cycle_id } = useParams();
  const [file, setFile] = useState([]);
  const { setToast: toast } = useToastStore();

  const { mutate: populate, isPending: uploading } = usePopulateCycleData(cycle_id);
  const { mutate: downloadDummy, isPending: downloadingDummy } = useDownloadDummyData();

  const handleDownloadDummy = () => {
    const selectedCycleStartDate = localStorage.getItem("selectedCycleStartDate");
    downloadDummy(selectedCycleStartDate, {
      onSuccess: (blob) => {
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "teramina_dummy_data.csv");
        document.body.appendChild(link);
        link.click();
        link.remove();
      },
      onError: () => toast({ open: true, variant: "error", text: t("DOWNLOAD_ERROR_MESSAGE") }),
    });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!file[0]) return;

    const source_type = file[0].type === "text/csv" ? "csv" : "xlsx";
    populate(
      { file: file[0], source_type },
      {
        onSuccess: async () => {
          await onClose();
          toast({ open: true, variant: "success", text: t("ADD_DATA_SUCCESS_MESSAGE") });
        },
        onError: (err) => {
          const message = err?.response?.data?.message;
          toast({ open: true, variant: "error", text: message ?? t("ADD_DATA_FAILED_MESSAGE") });
        },
      }
    );
  };

  return (
    <Box className={styles.modalWrapper}>
      <form onSubmit={handleSubmit} className={styles.modalContent}>
        <Typography className={styles.titleForm} variant="h5">
          {t("UPLOAD_CYCLE_DATA")}
        </Typography>
        <TeraminaDropzone
          changeFile={setFile}
          message={t("SUPPORTED_FORMAT_DOCUMENT")}
          multiple={false}
          accept={{
            "text/csv": [".csv"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
          }}
        />
        <Button
          type="submit"
          variant="contained"
          className={styles.btnSubmit}
          disabled={uploading}
        >
          {uploading && <CircularProgress color="inherit" classes={{ root: styles.circular }} />}
          {!uploading && t("UPLOAD_FILE")}
        </Button>
        <Button
          variant="text"
          onClick={handleDownloadDummy}
          disabled={downloadingDummy}
          style={{ textAlign: "center", display: "block", width: "100%", padding: 0, textTransform: "none" }}
        >
          <Typography variant="h6" component="span">
            {t("DOWNLOAD_EXAMPLE_DATA")}
          </Typography>
        </Button>
      </form>
    </Box>
  );
};

const ModalPopulateAdd = (props) => {
  const { t } = useTranslation();
  const { open, onOpen, onClose } = useModal();
  return (
    <Fragment>
      <Button onClick={onOpen} sx={{ color: "#161616", minWidth: "unset !important", background: "rgba(71, 77, 164, 0.32)", marginRight: "5px", borderRadius: "6px", padding: "10.5px", "&:hover": { color: "#161616", background: "rgba(71, 77, 164, 0.6)" }, "& svg": { width: "20px", height: "20px" } }}>{t("ADD_CYCLE_POPULATION")}</Button>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
        <DialogContent sx={{ padding: "0px !important" }}>
          <PopulateAdd {...props} onClose={onClose} />
        </DialogContent>
      </Dialog>
    </Fragment>
  );
};

export default ModalPopulateAdd;
