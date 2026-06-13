import { useState } from "react";
import {
  Button,
  Container,
  TextField,
  Typography,
  useMediaQuery,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import Footer from "components/footer";
import Language from "components/language";
import { useStyles } from "./styles";
import { useTranslation } from "react-i18next";
import { FaSignInAlt } from "react-icons/fa";
import { Link } from "react-router-dom";
import { requestBetaAccess } from "features/user/queries";

const Home = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const { classes: styles } = useStyles();
  const token = localStorage.getItem("authentication");
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const handleWaitlist = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setSubmitting(true);
    setSubmitError("");
    try {
      await requestBetaAccess(email.trim(), "landing");
      setSubmitted(true);
    } catch {
      setSubmitError("We could not submit your request. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const scrollToWaitlist = () => {
    document.getElementById("waitlist")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <>
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <Container fixed className={styles.containerHome}>
        <div className={styles.header}>
          <div className={styles.headerLogo}>
            <img src="/assets/images/logo-teramina3.svg" alt="logo" />
          </div>
          <div className={styles.wrapperBtnHomeHeader}>
            {!isMobile && <Button component={Link} to="/services">Services</Button>}
            {!isMobile && <Button component={Link} to="/knowledge">Knowledge</Button>}
            <Link to="/signin" className={styles.wrapperBtnLogin}>
              <Button variant="contained" className={styles.btnLoginTeal}>
                {isMobile ? <FaSignInAlt /> : (token ? t("OPEN_DASHBOARD") : t("HOME.HERO_CTA_SECONDARY"))}
              </Button>
            </Link>
            <Language />
          </div>
        </div>

        {/* ── Hero ──────────────────────────────────────────────────────── */}
        <div className={styles.hero}>
          <div className={styles.contentHero}>
            <Typography variant="h1" align="center" className={styles.textHeading}>
              {t("HOME.HERO_TITLE")}
            </Typography>
            <Typography variant="body1" align="center" className={styles.textContent}>
              {t("HOME.HERO_SUBTITLE")}
            </Typography>
            <div className={styles.heroCtas}>
              <Button
                variant="contained"
                className={styles.btnHeroPrimary}
                onClick={scrollToWaitlist}
              >
                {t("HOME.HERO_CTA_PRIMARY")}
              </Button>
            </div>
          </div>
        </div>
      </Container>

      {/* ── Social proof bar ──────────────────────────────────────────────── */}
      <section className={styles.sectionSocialProof}>
        <div className={styles.statsRow}>
          {[
            { val: t("HOME.SOCIAL.STAT_1_VALUE"), unit: t("HOME.SOCIAL.STAT_1_UNIT"), label: t("HOME.SOCIAL.STAT_1_LABEL") },
            { val: t("HOME.SOCIAL.STAT_2_VALUE"), unit: t("HOME.SOCIAL.STAT_2_UNIT"), label: t("HOME.SOCIAL.STAT_2_LABEL") },
            { val: t("HOME.SOCIAL.STAT_3_VALUE"), unit: t("HOME.SOCIAL.STAT_3_UNIT"), label: t("HOME.SOCIAL.STAT_3_LABEL") },
          ].map((stat, i) => (
            <div className={styles.statItem} key={i}>
              <Typography className={styles.statValue}>{stat.val}</Typography>
              <Typography className={styles.statUnit}>{stat.unit}</Typography>
              <Typography className={styles.statLabel}>{stat.label}</Typography>
            </div>
          ))}
        </div>
      </section>

      {/* ── Banner image ──────────────────────────────────────────────────── */}
      <section className={styles.sectionBanner}></section>

      {/* ── How it works ──────────────────────────────────────────────────── */}
      <section className={styles.sectionHowItWorks}>
        <Container fixed className={styles.containerHome}>
          <Typography className={styles.howTitle}>{t("HOME.HOW.TITLE")}</Typography>
          <div className={styles.stepsGrid}>
            {[
              { num: "01", title: t("HOME.HOW.STEP_1_TITLE"), desc: t("HOME.HOW.STEP_1_DESC") },
              { num: "02", title: t("HOME.HOW.STEP_2_TITLE"), desc: t("HOME.HOW.STEP_2_DESC") },
              { num: "03", title: t("HOME.HOW.STEP_3_TITLE"), desc: t("HOME.HOW.STEP_3_DESC") },
            ].map((step, i) => (
              <div className={styles.stepCard} key={i}>
                <div className={styles.stepBadge}>{step.num}</div>
                <Typography className={styles.stepTitle}>{step.title}</Typography>
                <Typography className={styles.stepDesc}>{step.desc}</Typography>
              </div>
            ))}
          </div>
        </Container>
      </section>

      {/* ── Feature section ───────────────────────────────────────────────── */}
      <section className={styles.sectionFeature}>
        <Container fixed className={styles.containerHome}>
          <div className={styles.featureSplitRow}>
            {/* Left column — text */}
            <div className={styles.featureTextCol}>
              <Typography className={styles.textHeadingFeature}>
                {t("HOME.SECTION_ONE.TITLE")}
              </Typography>
              <Typography className={styles.textContentFeature}>
                {t("HOME.SECTION_ONE.SUBTITLE")}
              </Typography>
              <div className={styles.featureItemsCol}>
                {[
                  { title: t("HOME.SECTION_ONE.CONTENT_1_TITLE"), sub: t("HOME.SECTION_ONE.CONTENT_1_SUBTITLE") },
                  { title: t("HOME.SECTION_ONE.CONTENT_2_TITLE"), sub: t("HOME.SECTION_ONE.CONTENT_2_SUBTITLE") },
                  { title: t("HOME.SECTION_ONE.CONTENT_3_TITLE"), sub: t("HOME.SECTION_ONE.CONTENT_3_SUBTITLE") },
                  { title: t("HOME.SECTION_ONE.CONTENT_4_TITLE"), sub: t("HOME.SECTION_ONE.CONTENT_4_SUBTITLE") },
                ].map((item, i) => (
                  <div className={styles.itemFeature} key={i}>
                    <Typography className={styles.textHeadingItemFeature}>
                      {item.title}
                    </Typography>
                    <Typography className={styles.textContentItemFeature}>
                      {item.sub}
                    </Typography>
                  </div>
                ))}
              </div>
            </div>
            {/* Right column — image */}
            <div className={styles.featureImgCol}>
              <img src="/assets/images/laptop.svg" alt="feature-img" style={{ width: "100%", display: "block" }} />
            </div>
          </div>
        </Container>
      </section>

      {/* ── Waitlist ──────────────────────────────────────────────────────── */}
      <div className={styles.waitlistSection} id="waitlist">
        <Typography variant="h1" align="center" className={styles.textHeading}>
          {t("HOME.SECTION_TWO.TITLE")}
        </Typography>
        <Typography variant="body1" align="center" className={styles.textContent}>
          {t("HOME.SECTION_TWO.SUBTITLE")}
        </Typography>
        {submitted ? (
          <Typography align="center" className={styles.waitlistSuccess}>
            {t("HOME.WAITLIST.SUCCESS")}
          </Typography>
        ) : (
          <form onSubmit={handleWaitlist} className={styles.waitlistForm}>
            <TextField
              className={styles.waitlistInput}
              size="small"
              type="email"
              placeholder={t("HOME.WAITLIST.EMAIL_PLACEHOLDER")}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Button
              type="submit"
              variant="contained"
              className={styles.waitlistBtn}
              disableElevation
              disabled={submitting}
            >
              {submitting ? "Submitting..." : t("HOME.WAITLIST.SUBMIT")}
            </Button>
            {submitError && <Typography color="error">{submitError}</Typography>}
          </form>
        )}
      </div>

      <Footer />
    </>
  );
};

export default Home;
