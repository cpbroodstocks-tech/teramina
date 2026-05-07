import { useParams } from "react-router-dom";
import { Button } from "@mui/material";
import { useStyles } from "./styles";
import { FaDownload } from "react-icons/fa";
import { useToastStore } from "store/toast.store";
import { useTranslation } from "react-i18next";
import { useDownloadCycleData } from "features/cycle-detail/queries";

const ButtonDownloadData = () => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { cycle_id } = useParams();
  const { setToast } = useToastStore();
  const { mutate: download, isPending: loading } = useDownloadCycleData(cycle_id);

  const handleClick = () => {
    download(undefined, {
      onSuccess: (blob) => {
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "data.csv");
        link.click();
        window.URL.revokeObjectURL(url);
      },
      onError: () => setToast({ open: true, variant: "error", text: t("DOWNLOAD_ERROR_MESSAGE") }),
    });
  };

  return (
    <div>
      <Button onClick={handleClick} className={styles.btnDownload} disabled={loading}>
        {loading ? (
          t("DOWNLOADING")
        ) : (
          <>
            <FaDownload className={styles.btnDownloadIcon} />
            {t("DOWNLOAD_DATA")}
          </>
        )}
      </Button>
    </div>
  );
};

export default ButtonDownloadData;
