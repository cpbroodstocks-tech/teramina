import { useState, Fragment } from "react";
import { useNavigate } from "react-router-dom";
import { Grid, TextField, Card, CardHeader, Typography, Button, CardContent, CardActions } from "@mui/material";
import { useStyles } from "pages/dashboard/cost_data/styles";
import { useTranslation } from "react-i18next";
import TeraminaDropzone from "components/dropzone";
import { BiChevronLeftCircle } from "react-icons/bi";
import { useParams } from "react-router-dom";
import { useToastStore } from "store/toast.store";
import { useUploadCostData } from "features/user/queries";

const CostData = () => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const navigate = useNavigate();
  const { farm_id } = useParams();
  const { setToast: toast } = useToastStore();
  const [file, setFile] = useState(null);
  const [formData, setFormData] = useState({ start_date: "", end_date: "" });
  const { mutate: uploadCost, isPending } = useUploadCostData();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!file?.[0]) return;
    uploadCost(
      { farm_id, start_date: formData.start_date, end_date: formData.end_date, file: file[0] },
      {
        onSuccess: () => toast({ open: true, variant: "success", text: "Success" }),
        onError: () => toast({ open: true, variant: "error", text: "Failed to add cost data" }),
      }
    );
  };

  return (
    <Fragment>
      <Typography variant="h5" className={styles.titlePage}>{t("MENU.COST_DATA")}</Typography>
      <div className={styles.container}>
        <Button className={styles.btnBack} onClick={() => navigate(-1)}>
          <BiChevronLeftCircle className={styles.btnBackIcon} />
          <Typography variant="span" className={styles.btnBackText}>Back</Typography>
        </Button>
        <Card>
          <CardHeader title="Cost Data" />
          <form onSubmit={handleSubmit}>
            <CardContent>
              <Grid container spacing={3} className={styles.dateSelector}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    id="start-date"
                    name="start_date"
                    label="Start Date"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    value={formData.start_date}
                    onChange={handleChange}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    id="end-date"
                    name="end_date"
                    label="End Date"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    value={formData.end_date}
                    onChange={handleChange}
                  />
                </Grid>
              </Grid>
              <TeraminaDropzone changeFile={setFile} />
            </CardContent>
            <CardActions disableSpacing className={styles.cardFooter}>
              <Button type="submit" variant="contained" disabled={isPending}>
                Upload
              </Button>
            </CardActions>
          </form>
        </Card>
      </div>
    </Fragment>
  );
};

export default CostData;
