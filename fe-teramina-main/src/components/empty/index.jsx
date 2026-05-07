import { useStyles } from "components/empty/styles";

const Empty = () => {
  const { classes: styles } = useStyles();

  return (
    <div className={styles.contentEmpty}>
      <div className={styles.lgEmpty}>
        <img src="/assets/images/empty.png" alt="empty" />
      </div>
    </div>
  );
};

export default Empty;
