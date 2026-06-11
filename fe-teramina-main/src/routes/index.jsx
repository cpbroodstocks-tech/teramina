import { lazy } from "react";

import { ReactSVG } from "react-svg";
import { Navigate } from "react-router-dom";
import OpacityIcon from "@mui/icons-material/Opacity";
import PsychologyIcon from "@mui/icons-material/Psychology";
import MenuBookIcon from "@mui/icons-material/MenuBook";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import TodayIcon from "@mui/icons-material/Today";
import TimelineIcon from "@mui/icons-material/Timeline";
import PrivateRoute from "routes/private";
import iconEconomics from "/assets/images/icons/economics.svg";
import iconFarm from "/assets/images/icons/farm.svg";
import iconFeeding from "/assets/images/icons/feeding.svg";
import iconForecast from "/assets/images/icons/forecast.svg";
import iconHarvest from "/assets/images/icons/harvest.svg";
import iconOverview from "/assets/images/icons/overview.svg";
import iconProfile from "/assets/images/icons/profile.svg";

const Home = lazy(() => import("pages/home"));
const SignIn = lazy(() => import("pages/signin"));
const NotFound = lazy(() => import("pages/notfound"));
const Services = lazy(() => import("pages/services"));
const Knowledge = lazy(() => import("pages/knowledge"));
const KnowledgeDetail = lazy(() => import("pages/knowledge/detail"));
const AdvisoryIntake = lazy(() => import("pages/advisory-intake"));
const Dashboard = lazy(() => import("pages/dashboard/home"));
const Profile = lazy(() => import("pages/dashboard/profile"));
const ProfileEdit = lazy(() => import("pages/dashboard/profile_edit"));
const CostData = lazy(() => import("pages/dashboard/cost_data"));
const FarmManagement = lazy(() => import("pages/dashboard/farm-management"));
const Pond = lazy(() => import("pages/dashboard/pond"));
const Cycle = lazy(() => import("pages/dashboard/cycle"));
const CycleDetail = lazy(() => import("pages/dashboard/cycle_detail"));
const Overview = lazy(() => import("widgets/overview"));
const Feeding = lazy(() => import("widgets/feeding"));
const Forecast = lazy(() => import("widgets/forecast"));
const Economics = lazy(() => import("widgets/economics"));
const Harvest = lazy(() => import("widgets/harvest"));
const WaterQuality = lazy(() => import("widgets/water-quality"));
const HarvestSimulator = lazy(() => import("widgets/harvest-simulator"));
const PLReport = lazy(() => import("pages/dashboard/pl_report"));
const FarmPLReport = lazy(() => import("pages/dashboard/farm_pl_report"));
const Memory = lazy(() => import("pages/dashboard/memory"));
const Library = lazy(() => import("pages/dashboard/library"));
const Advisory = lazy(() => import("pages/dashboard/advisory"));
const Billing = lazy(() => import("pages/dashboard/billing"));
const AdvisoryNew = lazy(() => import("pages/dashboard/advisory_new"));
const AdvisoryDetail = lazy(() => import("pages/dashboard/advisory_detail"));
const CommercialAdmin = lazy(() => import("pages/dashboard/commercial_admin"));
const TodayView = lazy(() => import("pages/dashboard/today"));
const PondTimeline = lazy(() => import("pages/dashboard/pond-timeline"));
const SharePage = lazy(() => import("pages/share"));

const routes = [
  {
    path: "*",
    label: "404",
    element: <NotFound />,
  },
  {
    path: "/",
    label: "LOGIN",
    element: <Home />,
  },
  {
    path: "/signin",
    label: "SIGN_IN",
    element: <SignIn />,
  },
  {
    path: "/signup",
    label: "SIGN_UP",
    element: <Navigate to="/signin" replace />,
  },
  {
    path: "/services",
    label: "SERVICES",
    element: <Services />,
  },
  {
    path: "/knowledge",
    label: "KNOWLEDGE",
    element: <Knowledge />,
  },
  {
    path: "/knowledge/:slug",
    label: "KNOWLEDGE",
    element: <KnowledgeDetail />,
  },
  {
    path: "/advisory/intake/:service_slug",
    label: "ADVISORY",
    element: <AdvisoryIntake />,
  },
  {
    path: "/dashboard",
    element: (
      <PrivateRoute>
        <Dashboard />
      </PrivateRoute>
    ),
    children: [
      {
        path: "",
        label: "MENU.OVERVIEW",
        element: <Overview />,
        icon: <ReactSVG src={iconOverview} />,
        category: "parrent",
      },
      {
        path: "farm",
        label: "MENU.FARM_MANAGEMENT",
        element: <Navigate to="/dashboard/farm-management" replace />,
        icon: <ReactSVG src={iconFarm} />,
        category: "children",
      },
      {
        path: "farm-management",
        label: "MENU.FARM_MANAGEMENT",
        element: <FarmManagement />,
        icon: <ReactSVG src={iconFarm} />,
        category: "parrent",
      },
      {
        path: "pond/:farm_id",
        label: "MENU.FARM_MANAGEMENT",
        element: <Pond />,
        icon: <ReactSVG src={iconFarm} />,
        category: "children",
      },
      {
        path: "cycle/:pond_id",
        label: "MENU.FARM_MANAGEMENT",
        element: <Cycle />,
        icon: <ReactSVG src={iconFarm} />,
        category: "children",
      },
      {
        path: "cycle/detail/:cycle_id",
        label: "MENU.FARM_MANAGEMENT",
        element: <CycleDetail />,
        icon: <ReactSVG src={iconFarm} />,
        category: "children",
      },
      {
        path: "economics",
        label: "MENU.COST_ACCOUNTING",
        element: <Economics />,
        icon: <ReactSVG src={iconEconomics} />,
        category: "parrent",
      },
      {
        path: "feeding",
        label: "MENU.FEEDING",
        element: <Feeding />,
        icon: <ReactSVG src={iconFeeding} />,
        category: "parrent",
      },
      {
        path: "forecast",
        label: "MENU.FORECAST",
        element: <Forecast />,
        icon: <ReactSVG src={iconForecast} />,
        category: "parrent",
      },
      {
        path: "harvest",
        label: "MENU.HARVEST",
        element: <Harvest />,
        icon: <ReactSVG src={iconHarvest} />,
        category: "parrent",
      },
      {
        path: "water-quality",
        label: "MENU.WATER_QUALITY",
        element: <WaterQuality />,
        icon: <OpacityIcon fontSize="small" />,
        category: "parrent",
      },
      {
        path: "today",
        label: "MENU.TODAY",
        element: <TodayView />,
        icon: <TodayIcon fontSize="small" />,
        category: "parrent",
      },
      {
        path: "memory",
        label: "MENU.MEMORY",
        element: <Memory />,
        icon: <PsychologyIcon fontSize="small" />,
        category: "parrent",
      },
      {
        path: "library",
        label: "MENU.LIBRARY",
        element: <Library />,
        icon: <MenuBookIcon fontSize="small" />,
        category: "parrent",
      },
      {
        path: "advisory",
        label: "MENU.ADVISORY",
        element: <Advisory />,
        icon: <SupportAgentIcon fontSize="small" />,
        category: "parrent",
      },
      {
        path: "advisory/new",
        label: "MENU.ADVISORY",
        element: <AdvisoryNew />,
        icon: <SupportAgentIcon fontSize="small" />,
        category: "children",
      },
      {
        path: "advisory/:case_id",
        label: "MENU.ADVISORY",
        element: <AdvisoryDetail />,
        icon: <SupportAgentIcon fontSize="small" />,
        category: "children",
      },
      {
        path: "billing",
        label: "MENU.BILLING",
        element: <Billing />,
        icon: <ReceiptLongIcon fontSize="small" />,
        category: "parrent",
      },
      {
        path: "commercial-admin",
        label: "MENU.COMMERCIAL_ADMIN",
        element: <CommercialAdmin />,
        icon: <AdminPanelSettingsIcon fontSize="small" />,
        category: "parrent",
        adminOnly: true,
      },
      {
        path: "pond-timeline/:cycle_id",
        label: "MENU.POND_TIMELINE",
        element: <PondTimeline />,
        icon: <TimelineIcon fontSize="small" />,
        category: "children",
      },
      {
        path: "profile",
        label: "MENU.PROFILE",
        element: <Profile />,
        icon: <ReactSVG src={iconProfile} />,
        category: "parrent",
      },
      {
        path: "profile/edit",
        label: "MENU.PROFILE",
        element: <ProfileEdit />,
        icon: <ReactSVG src={iconProfile} />,
        category: "children",
      },
      {
        path: "cost-data/:farm_id",
        label: "MENU.COST_DATA",
        element: <CostData />,
        icon: <ReactSVG src={iconProfile} />,
        category: "children",
      },
      {
        path: "harvest-simulator/:cycle_id",
        label: "MENU.HARVEST_SIMULATOR",
        element: <HarvestSimulator />,
        icon: <ReactSVG src={iconHarvest} />,
        category: "children",
      },
      {
        path: "cycle/pl-report/:cycle_id",
        label: "MENU.PL_REPORT",
        element: <PLReport />,
        icon: <ReactSVG src={iconEconomics} />,
        category: "children",
      },
      {
        path: "farm/pl-report/:farm_id",
        label: "MENU.PL_REPORT",
        element: <FarmPLReport />,
        icon: <ReactSVG src={iconEconomics} />,
        category: "children",
      },
    ],
  },
  {
    path: "/share/:token",
    label: "SHARE",
    element: <SharePage />,
  },
];

export { routes };
