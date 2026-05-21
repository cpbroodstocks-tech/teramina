import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  containerHome: {
    marginBottom: "0",
    [theme.breakpoints.up("500")]: {
      maxWidth: "900px",
    },
    [theme.breakpoints.up("1025")]: {
      maxWidth: "1024px",
    },
    [theme.breakpoints.up("1300")]: {
      maxWidth: "1270px",
    },
    [theme.breakpoints.up("1500")]: {
      maxWidth: "1366px",
    },
  },
  header: {
    marginTop: "20px",
    marginBottom: "20px",
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerLogo: {
    display: "flex",
  },
  wrapperBtnLogin: {
    dusplay: "flex",
  },
  wrapperBtnHomeHeader: {
    display: "flex",
    justifyContent: "flex-end",
    alignItems: "center",
    gap: "12px",
  },
  btnLogin: {
    border: "3px solid #474DA4",
    borderRadius: "15px",
    padding: "12px 43px",
    fontFamily: "Lato",
    fontSize: "18px",
    lineHeight: "normal",
    [theme.breakpoints.between("481", "1025")]: {
      fontSize: "14px",
      padding: "8px 30px",
    },
    [theme.breakpoints.down("480")]: {
      fontSize: "20px",
      border: "none",
      padding: "10px 16px",
    },
  },
  hero: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    width: "100%",
    marginTop: "48px",
    marginBottom: "16px",
    [theme.breakpoints.between("481", "1025")]: {
      marginTop: "32px",
    },
    [theme.breakpoints.down("sm")]: {
      marginTop: "32px",
    },
  },
  contentHero: {
    width: "83%",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    [theme.breakpoints.down("sm")]: {
      width: "100%",
    },
  },
  textHeading: {
    fontFamily: "Lato",
    fontWeight: "700",
    fontSize: "58px",
    [theme.breakpoints.down("sm")]: {
      fontSize: "32px",
    },
    [theme.breakpoints.between("sm", "md")]: {
      fontSize: "32px",
    },
    [theme.breakpoints.between("481", "1025")]: {
      fontSize: "36px",
      padding: "0 20px",
    },
  },
  textContent: {
    fontFamily: "Lato",
    fontWeight: "400",
    fontSize: "24px",
    marginTop: "30px",
    [theme.breakpoints.down("sm")]: {
      padding: "0",
      fontSize: "18px",
    },
    [theme.breakpoints.between("sm", "md")]: {
      fontSize: "14px",
    },
    [theme.breakpoints.between("481", "1025")]: {
      padding: "0 70px",
      fontSize: "14px",
      marginTop: "15px",
    },
  },
  wrapperBtnContactUs: {
    marginTop: "43px",
    display: "flex",
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    [theme.breakpoints.between("481", "1025")]: {
      marginTop: "30px",
    },
  },
  btnContactUs: {
    fontFamily: "Lato",
    fontWeight: "700",
    fontSize: "24px",
    padding: "20px 70px",
    borderRadius: "15px",
    [theme.breakpoints.down("sm")]: {
      padding: "5px 40px",
    },
    [theme.breakpoints.between("481", "1025")]: {
      fontSize: "14px",
      padding: "8px 30px",
    },
  },

  sectionBanner: {
    display: "flex",
    minHeight: "100vh",
    backgroundImage: "url(/assets/images/img1.svg)",
    backgroundRepeat: "no-repeat",
    backgroundSize: "cover",
    backgroundPosition: "top",
    position: "relative",
    [theme.breakpoints.down("sm")]: {
      minHeight: "50vh  ",
    },
    [theme.breakpoints.between("481", "1025")]: {
      minHeight: "50vh  ",
      backgroundSize: "contain",
    },
    "&::after": {
      content: "\"\"",
      position: "absolute",
      display: "block",
      width: "100%",
      height: "50%",
      bottom: "0",
      background:
        "linear-gradient(180deg, rgba(71, 77, 164, 0) 0%, #474DA4 66.15%)",
    },
  },

  sectionFeature: {
    backgroundColor: "#474DA4",
    padding: "80px 0",
    [theme.breakpoints.down("sm")]: {
      padding: "48px 0",
    },
  },
  wrapperFeature: {},

  // 2-column split: text left, image right — no absolute positioning
  featureSplitRow: {
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    gap: "48px",
    marginTop: "64px",
    [theme.breakpoints.down("md")]: {
      flexDirection: "column",
      gap: "40px",
      marginTop: "40px",
    },
  },
  featureTextCol: {
    flex: "0 0 42%",
    maxWidth: "42%",
    [theme.breakpoints.down("md")]: {
      flex: "1 1 auto",
      maxWidth: "100%",
    },
  },
  featureImgCol: {
    flex: "1 1 auto",
    minWidth: "0",
    [theme.breakpoints.down("md")]: {
      display: "none",
    },
  },
  featureItemsCol: {
    marginTop: "40px",
    display: "flex",
    flexDirection: "column",
    gap: "0",
  },

  textHeadingFeature: {
    fontFamily: "Lato",
    fontWeight: "700",
    fontSize: "40px",
    color: "#fff",
    lineHeight: 1.2,
    [theme.breakpoints.down("sm")]: {
      fontSize: "28px",
    },
    [theme.breakpoints.between("481", "1025")]: {
      fontSize: "28px",
    },
  },
  textContentFeature: {
    color: "#a5b4cb",
    fontFamily: "Lato",
    fontWeight: "400",
    fontSize: "18px",
    marginTop: "16px",
    lineHeight: 1.6,
    [theme.breakpoints.down("sm")]: {
      fontSize: "15px",
    },
    [theme.breakpoints.between("481", "1025")]: {
      fontSize: "14px",
    },
  },

  itemFeature: {
    padding: "20px 0 20px 20px",
    borderLeft: "3px solid rgba(255,255,255,0.15)",
    marginBottom: "8px",
    transition: "border-color 0.2s",
    "&:hover": {
      borderLeft: "3px solid #2EC4B6",
    },
  },
  textHeadingItemFeature: {
    fontFamily: "Lato",
    fontWeight: "700",
    fontSize: "14px",
    color: "#fff",
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    [theme.breakpoints.down("sm")]: {
      fontSize: "13px",
    },
  },
  textContentItemFeature: {
    color: "#a5b4cb",
    fontFamily: "Lato",
    fontWeight: "400",
    fontSize: "15px",
    marginTop: "6px",
    lineHeight: 1.6,
    [theme.breakpoints.down("sm")]: {
      fontSize: "14px",
    },
  },
  waitlistSection: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "100px 24px",
    maxWidth: "720px",
    margin: "0 auto",
    [theme.breakpoints.down("sm")]: {
      padding: "60px 16px",
    },
  },

  // ── Sign-in button ─────────────────────────────────────────────────────────
  btnLoginTeal: {
    backgroundColor: "#2EC4B6",
    color: "#fff",
    borderRadius: "15px",
    padding: "12px 43px",
    fontFamily: "Lato",
    fontSize: "18px",
    lineHeight: "normal",
    border: "none",
    "&:hover": {
      backgroundColor: "#25b0a3",
    },
    [theme.breakpoints.between("481", "1025")]: {
      fontSize: "14px",
      padding: "8px 30px",
    },
    [theme.breakpoints.down("480")]: {
      fontSize: "20px",
      padding: "10px 16px",
    },
  },

  // ── Hero CTAs ──────────────────────────────────────────────────────────────
  heroCtas: {
    marginTop: "43px",
    display: "flex",
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: "16px",
    flexWrap: "wrap",
    [theme.breakpoints.between("481", "1025")]: {
      marginTop: "30px",
    },
  },
  btnHeroPrimary: {
    fontFamily: "Lato",
    fontWeight: "700",
    fontSize: "20px",
    padding: "16px 56px",
    borderRadius: "15px",
    backgroundColor: "#2EC4B6",
    color: "#fff",
    "&:hover": {
      backgroundColor: "#25b0a3",
    },
    [theme.breakpoints.down("sm")]: {
      padding: "10px 32px",
      fontSize: "16px",
    },
    [theme.breakpoints.between("481", "1025")]: {
      fontSize: "14px",
      padding: "8px 30px",
    },
  },
  btnHeroSecondary: {
    fontFamily: "Lato",
    fontWeight: "700",
    fontSize: "20px",
    padding: "16px 56px",
    borderRadius: "15px",
    border: "2px solid #474DA4",
    color: "#474DA4",
    [theme.breakpoints.down("sm")]: {
      padding: "10px 32px",
      fontSize: "16px",
    },
    [theme.breakpoints.between("481", "1025")]: {
      fontSize: "14px",
      padding: "8px 30px",
    },
  },

  // ── Social proof bar ───────────────────────────────────────────────────────
  sectionSocialProof: {
    borderTop: "1px solid #e8eaf0",
    borderBottom: "1px solid #e8eaf0",
    padding: "40px 24px",
    backgroundColor: "#fff",
    display: "flex",
    justifyContent: "center",
  },
  statsRow: {
    display: "flex",
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "stretch",
    maxWidth: "720px",
    width: "100%",
    [theme.breakpoints.down("sm")]: {
      flexDirection: "column",
    },
  },
  statItem: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    flex: "1",
    padding: "8px 32px",
    borderRight: "1px solid #e8eaf0",
    "&:last-child": {
      borderRight: "none",
    },
    [theme.breakpoints.down("sm")]: {
      borderRight: "none",
      borderBottom: "1px solid #e8eaf0",
      padding: "20px 16px",
      "&:last-child": {
        borderBottom: "none",
      },
    },
  },
  statValue: {
    fontFamily: "Lato",
    fontWeight: "800",
    fontSize: "52px",
    color: "#474DA4",
    lineHeight: 1,
    [theme.breakpoints.down("sm")]: {
      fontSize: "36px",
    },
  },
  statUnit: {
    fontFamily: "Lato",
    fontWeight: "700",
    fontSize: "12px",
    color: "#2EC4B6",
    textTransform: "uppercase",
    letterSpacing: "0.12em",
    marginTop: "6px",
  },
  statLabel: {
    fontFamily: "Lato",
    fontWeight: "400",
    fontSize: "13px",
    color: "#888",
    marginTop: "8px",
    textAlign: "center",
    maxWidth: "180px",
    lineHeight: 1.4,
  },

  // ── How it works ───────────────────────────────────────────────────────────
  sectionHowItWorks: {
    backgroundColor: "#f8f9fc",
    padding: "80px 0",
    [theme.breakpoints.down("sm")]: {
      padding: "48px 0",
    },
  },
  howTitle: {
    fontFamily: "Lato",
    fontWeight: "700",
    fontSize: "36px",
    color: "#1A1D3B",
    textAlign: "center",
    marginBottom: "48px",
    [theme.breakpoints.down("sm")]: {
      fontSize: "26px",
      marginBottom: "32px",
    },
  },
  stepsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "24px",
    [theme.breakpoints.down("md")]: {
      gridTemplateColumns: "1fr",
      gap: "16px",
    },
  },
  stepCard: {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    padding: "32px",
    backgroundColor: "#fff",
    borderRadius: "12px",
    border: "1px solid #e8eaf0",
  },
  stepBadge: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: "40px",
    height: "40px",
    borderRadius: "50%",
    backgroundColor: "#474DA4",
    color: "#fff",
    fontFamily: "Lato",
    fontWeight: "800",
    fontSize: "14px",
    marginBottom: "20px",
    flexShrink: 0,
  },
  stepTitle: {
    fontFamily: "Lato",
    fontWeight: "700",
    fontSize: "18px",
    color: "#1A1D3B",
    marginBottom: "10px",
  },
  stepDesc: {
    fontFamily: "Lato",
    fontWeight: "400",
    fontSize: "15px",
    color: "#666",
    lineHeight: 1.6,
  },

  // ── Waitlist section ───────────────────────────────────────────────────────
  waitlistForm: {
    display: "flex",
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "stretch",
    gap: "0",
    marginTop: "32px",
    maxWidth: "520px",
    width: "100%",
    [theme.breakpoints.down("sm")]: {
      flexDirection: "column",
      gap: "12px",
    },
  },
  waitlistInput: {
    flex: 1,
    "& .MuiOutlinedInput-root": {
      borderRadius: "15px 0 0 15px",
      backgroundColor: "#fff",
      [theme.breakpoints.down("sm")]: {
        borderRadius: "15px",
      },
    },
  },
  waitlistBtn: {
    fontFamily: "Lato",
    fontWeight: "700",
    fontSize: "16px",
    padding: "0 32px",
    borderRadius: "0 15px 15px 0",
    backgroundColor: "#2EC4B6",
    color: "#fff",
    whiteSpace: "nowrap",
    flexShrink: 0,
    "&:hover": {
      backgroundColor: "#25b0a3",
    },
    [theme.breakpoints.down("sm")]: {
      borderRadius: "15px",
      padding: "12px 24px",
    },
  },
  waitlistSuccess: {
    fontFamily: "Lato",
    fontWeight: "600",
    fontSize: "18px",
    color: "#2EC4B6",
    marginTop: "24px",
  },
}));

export { useStyles };
