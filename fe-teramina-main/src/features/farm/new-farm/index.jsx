import { Fragment, useEffect, useState } from "react";
import {
  Typography,
  TextField,
  Button,
  MenuItem,
  CircularProgress,
} from "@mui/material";
import classNames from "classnames";
import { useStyles } from "features/farm/new-farm/styles";
import axios from "axios";
import startCase from "lodash/startCase";
import toLower from "lodash/toLower";
import { useTranslation } from "react-i18next";

const fetchCityRegion = async (url) => {
  const response = await axios.get(url);
  if (!response) throw new Error("Failed to fetch city region");
  return response.data;
};

const NewFarm = (props) => {
  const {
    formik,
    formTitle = "CREATE_NEW_FARM",
    actionText = "SUBMIT",
    isModalComponent = false,
    handleBack,
  } = props;

  const { t } = useTranslation();
  const { classes: styles } = useStyles();

  const [cityRegion, setCityRegion] = useState(() => ({
    provinsi: [],
    kabupaten: [],
    kecamatan: [],
    kelurahan: [],
  }));

  const handleCityRegionFormChange = async (key, data) => {
    let fields = [];
    const { id, name } = data ? JSON.parse(data) : { id: "", name: "" };
    switch (key) {
    case "provinsi":
      fields = ["kabupaten", "kecamatan", "kelurahan"];
      break;
    case "kabupaten":
      fields = ["kecamatan", "kelurahan"];
      break;
    case "kecamatan":
      fields = ["kelurahan"];
      break;
    case "kelurahan":
      fields = [];
      break;
    default:
      fields = [];
      break;
    }

    const indexToExclude = fields.indexOf(key);
    if (indexToExclude > -1) fields.splice(indexToExclude, 1);

    for (let field of fields) {
      formik.setValue(field, "");
    }

    if (fields[0]) {
      let resetCityRegency = {};
      for (const field of fields) {
        resetCityRegency[field] = [];
      }

      if (id && name) {
        const response = await fetchCityRegion(
          `/api/${[fields[0]]}/${id}.json`
        );

        setCityRegion((previousValue) => ({
          ...previousValue,
          ...resetCityRegency,
          [`${fields[0]}`]: response,
        }));
      } else {
        setCityRegion((previousValue) => ({
          ...previousValue,
          ...resetCityRegency,
        }));
      }
    }

    formik.setValue(
      key,
      id && name ? JSON.stringify({ id: id, name: name }) : ""
    );
  };

  useEffect(() => {
    fetchCityRegion("/api/provinsi.json").then((data) =>
      setCityRegion((previousValue) => ({
        ...previousValue,
        provinsi: data,
      }))
    );
  }, []);

  return (
    <Fragment>
      <form className={styles.container} onSubmit={formik.handleSubmit}>
        <Typography variant="h5" className={styles.title}>
          {t(formTitle)}
        </Typography>
        <Typography
          variant="h6"
          className={classNames(styles.label, styles.requiredLabel)}
        >
          {t("YOUR_FARM_NAME")}
        </Typography>
        <TextField
          variant="outlined"
          className={styles.input}
          error={!!formik.formState.errors.name}
          helperText={formik.formState.errors.name?.message}
          {...formik.register("name")}
        />
        <Typography
          variant="h6"
          className={classNames(styles.label, styles.requiredLabel)}
        >
          {t("YOUR_FARM_PROVINCE")}
        </Typography>
        <TextField
          id="provinsiField"
          select
          variant="outlined"
          className={styles.input}
          value={formik.watch("provinsi")}
          onChange={({ target: { value } }) =>
            handleCityRegionFormChange("provinsi", value)
          }
          error={!!formik.formState.errors.provinsi}
          helperText={formik.formState.errors.provinsi?.message}
          disabled={!cityRegion?.provinsi?.length}
        >
          <MenuItem disabled value="">
            <em>{t("NONE")}</em>
          </MenuItem>
          {cityRegion.provinsi.map((provinsi, index) => (
            <MenuItem
              value={JSON.stringify({
                id: provinsi.id,
                name: startCase(toLower(provinsi.nama)),
              })}
              key={index}
            >
              {startCase(toLower(provinsi.nama))}
            </MenuItem>
          ))}
        </TextField>
        <Typography
          variant="h6"
          className={classNames(styles.label, styles.requiredLabel)}
        >
          {t("YOUR_FARM_CITY")}
        </Typography>
        <TextField
          id="kabupatenField"
          select
          variant="outlined"
          className={styles.input}
          value={formik.watch("kabupaten")}
          onChange={({ target: { value } }) =>
            handleCityRegionFormChange("kabupaten", value)
          }
          error={!!formik.formState.errors.kabupaten}
          helperText={formik.formState.errors.kabupaten?.message}
          disabled={!cityRegion?.kabupaten?.length}
        >
          <MenuItem disabled value="">
            <em>{t("NONE")}</em>
          </MenuItem>
          {cityRegion.kabupaten.map((kabupaten, index) => (
            <MenuItem
              value={JSON.stringify({
                id: kabupaten.id,
                name: startCase(toLower(kabupaten.nama)),
              })}
              key={index}
            >
              {startCase(toLower(kabupaten.nama))}
            </MenuItem>
          ))}
        </TextField>
        <Typography
          variant="h6"
          className={classNames(styles.label, styles.requiredLabel)}
        >
          {t("YOUR_FARM_DISTRICT")}
        </Typography>
        <TextField
          id="kecamatanField"
          select
          variant="outlined"
          className={styles.input}
          value={formik.watch("kecamatan")}
          onChange={({ target: { value } }) =>
            handleCityRegionFormChange("kecamatan", value)
          }
          error={!!formik.formState.errors.kecamatan}
          helperText={formik.formState.errors.kecamatan?.message}
          disabled={!cityRegion?.kecamatan?.length}
        >
          <MenuItem disabled value="">
            <em>{t("NONE")}</em>
          </MenuItem>
          {cityRegion.kecamatan.map((kecamatan, index) => (
            <MenuItem
              value={JSON.stringify({
                id: kecamatan.id,
                name: startCase(toLower(kecamatan.nama)),
              })}
              key={index}
            >
              {startCase(toLower(kecamatan.nama))}
            </MenuItem>
          ))}
        </TextField>
        <Typography
          variant="h6"
          className={classNames(styles.label, styles.requiredLabel)}
        >
          {t("YOUR_FARM_VILLAGE")}
        </Typography>
        <TextField
          id="kelurahanField"
          select
          variant="outlined"
          className={styles.input}
          value={formik.watch("kelurahan")}
          onChange={({ target: { value } }) =>
            handleCityRegionFormChange("kelurahan", value)
          }
          error={!!formik.formState.errors.kelurahan}
          helperText={formik.formState.errors.kelurahan?.message}
          disabled={!cityRegion?.kelurahan?.length}
        >
          <MenuItem disabled value="">
            <em>{t("NONE")}</em>
          </MenuItem>
          {cityRegion.kelurahan.map((kelurahan, index) => (
            <MenuItem
              value={JSON.stringify({
                id: kelurahan.id,
                name: startCase(toLower(kelurahan.nama)),
              })}
              key={index}
            >
              {startCase(toLower(kelurahan.nama))}
            </MenuItem>
          ))}
        </TextField>
        <div className={styles.btnContainer}>
          {handleBack && (
            <Button
              variant="contained"
              className={styles.btnBack}
              onClick={() => {
                handleBack && handleBack();
              }}
            >
              {t("BACK")}
            </Button>
          )}
          {isModalComponent && (
            <Button
              type="submit"
              variant="contained"
              className={styles.btnSubmit}
              disabled={formik.formState.isSubmitting}
            >
              {formik.formState.isSubmitting ? (
                <CircularProgress
                  color="inherit"
                  classes={{ root: styles.circular }}
                />
              ) : (
                t(actionText)
              )}
            </Button>
          )}
          {!isModalComponent && (
            <Button
              type="submit"
              variant="contained"
              className={styles.btnSubmit}
            >
              {t(actionText)}
            </Button>
          )}
        </div>
      </form>
    </Fragment>
  );
};

export default NewFarm;
