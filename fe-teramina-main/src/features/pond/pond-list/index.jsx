import { Fragment, useMemo, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Tooltip,
  Typography,
} from "@mui/material";
import EastIcon from "@mui/icons-material/East";
import { BiChevronLeftCircle } from "react-icons/bi";
import { TbUpload, TbDownload } from "react-icons/tb";
import { useNavigate } from "react-router-dom";
import ModalPondAdd from "features/pond/modal-add-pond";
import ModalPondEdit from "features/pond/modal-edit-pond";
import ModalPondDelete from "features/pond/modal-delete-pond";
import { useStyles } from "features/pond/pond-list/styles";
import Search from "components/search";
import { useDebounce } from "hooks/useDebounce";
import { useTranslation } from "react-i18next";
import { useToastStore } from "store/toast.store";
import { useDownloadPLReport } from "features/pond/queries";

const PondList = ({ data }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { classes: styles } = useStyles();
  const [search, setSearch] = useState("");
  const { setToast: toast } = useToastStore();
  const { mutate: downloadPLReport } = useDownloadPLReport();

  const handleSearchChange = useDebounce(
    (event) => setSearch(event.target.value),
    1000
  );

  const downloadReport = () => {
    downloadPLReport(data.farm_id, {
      onSuccess: (blob) => {
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "pl_report.xlsx");
        document.body.appendChild(link);
        link.click();
        window.URL.revokeObjectURL(url);
      },
      onError: () => toast({ open: true, variant: "error", text: "Failed to download report" }),
    });
  };

  const table = useMemo(() => {
    if (!search) return data.data;
    return data.data.filter((pond) =>
      pond.name.toLowerCase().includes(search.toLowerCase())
    );
  }, [search]);

  return (
    <Fragment>
      <Typography variant="h2" className={styles.pageTitle}>
        {t("DATA_MANAGEMENT")}
      </Typography>
      <Typography variant="h3" className={styles.sectionTitle}>
        {t("POND_LIST_IN_FARM", { name: data.farm_name })}
      </Typography>
      <Button className={styles.btnBack} onClick={() => navigate(-1)}>
        <BiChevronLeftCircle className={styles.btnBackIcon} />
        <Typography variant="span" className={styles.btnBackText}>
          {t("BACK_TO_FARM_LIST")}
        </Typography>
      </Button>
      {/* Pop Up Add Pond */}
      <div className={styles.toolbarTable}>
        <div className={styles.leftSection}>
          <ModalPondAdd data={data} />
          <Tooltip title="Download the P&L report">
            <Button className={styles.btnUploadDownload} onClick={downloadReport}>
              <TbDownload className={styles.btnIconUploadDownload} />
            </Button>
          </Tooltip>
          <Tooltip title="Upload the P&L report">
            <Button 
              className={styles.btnUploadDownload} 
              onClick={() =>
                navigate(`/dashboard/cost-data/${data.farm_id}`)
              }  
            >
              <TbUpload className={styles.btnIconUploadDownload} />
            </Button>
          </Tooltip>
        </div>
        <Search onChange={handleSearchChange} />
      </div>
      {/* List Pond */}
      <TableContainer component={Paper}>
        <Table className={styles.table}>
          <TableHead>
            <TableRow>
              <TableCell>{t("POND_NAME")}</TableCell>
              <TableCell>{t("POND_CONSTRUCTION")}</TableCell>
              <TableCell>{t("POND_SHAPE")}</TableCell>
              <TableCell>{t("STATUS")}</TableCell>
              <TableCell>&nbsp;</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {table.map((pond, key) => (
              <TableRow key={key}>
                <TableCell>{pond.name}</TableCell>
                <TableCell>{pond.pond_construction}</TableCell>
                <TableCell>{pond.pond_shape}</TableCell>
                <TableCell>
                  {pond.is_active ? "Aktif" : "Tidak Aktif"}
                </TableCell>
                <TableCell>
                  <div className={styles.actionContainer}>
                    <ModalPondEdit data={pond} />
                    <ModalPondDelete data={pond} />
                    <Button
                      className={styles.btnViewMore}
                      onClick={() => navigate(`/dashboard/cycle/${pond._id}`)}
                    >
                      <Typography
                        variant="span"
                        className={styles.btnViewMoreText}
                      >
                        {t("VIEW_MORE")}
                      </Typography>
                      <EastIcon className={styles.btnViewMoreIcon} />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Fragment>
  );
};

export default PondList;
