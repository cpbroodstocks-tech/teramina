import Footer from "components/footer";
import { useStyles } from "pages/home/styles";
import { Container, Typography, Button } from "@mui/material";
import { Link } from "react-router-dom";

const Home = () => {
  const { classes: styles } = useStyles();

  return (
    <>
      <Container fixed className={styles.containerHome}>
        <div className={styles.contentHome}>
          <div className={styles.leftContent}>
            <Typography
              variant="h2"
              component="h2"
              className={styles.headingHome}
            >
              Powerful analysis for shrimp farming operations
            </Typography>
            <Typography
              variant="p"
              component="p"
              className={styles.captionHome}
            >
              Teramina provides the state-of-the-art computational ecological
              shrimp farm modeling to help shrimp farmers optimize their shrimp
              farm management
            </Typography>
            <Link to="/signin">
              <Button variant="contained" className={styles.btnSignUp}>
                Get Started
              </Button>
            </Link>
          </div>
          <div className={styles.rightContent}>
            <img
              src="/assets/images/Intersect.png"
              className={styles.lgIntersect}
              alt="intersect"
            />
          </div>
        </div>
      </Container>
      <Footer />
    </>
  );
};

export default Home;
