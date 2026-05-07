import TextField from "@mui/material/TextField";
import SearchIcon from "@mui/icons-material/Search";
import { useStyles } from "components/search/styles";
import { useTranslation } from "react-i18next";

const Search = ({ onChange }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();

  return (
    <div className={styles.wrapperSearch}>
      <TextField
        label={t("SEARCH")}
        variant="outlined"
        onChange={onChange}
        inputProps={{
          style: {
            height: "24px",
          },
        }}
      />
      <i className={styles.bgIcon}>
        <SearchIcon />
      </i>
    </div>
  );
};

export default Search;
