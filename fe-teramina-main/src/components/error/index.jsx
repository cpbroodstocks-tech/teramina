import { useStyles } from "components/error/styles";

const Error = () => {
  const { classes: styles } = useStyles();

  return (
    <div className={styles.contentError}>
      <div className={styles.lgError}>
        <img src="/assets/images/error.png" alt="Error" />
      </div>
    </div>
  );
};

export default Error;
