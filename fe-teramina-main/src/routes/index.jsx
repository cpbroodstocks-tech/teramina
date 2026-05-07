import { lazy } from "react";

import { ReactSVG } from "react-svg";
import PrivateRoute from "routes/private";
import iconEconomics from "/assets/images/icons/economics.svg";
import iconFarm from "/assets/images/icons/farm.svg";
import iconFeeding from "/assets/images/icons/feeding.svg";
import iconForecast from "/assets/images/icons/forecast.svg";
import iconHarvest from "/assets/images/icons/harvest.svg";
import iconOverview from "/assets/images/icons/overview.svg";
import iconProfile from "/assets/images/icons/profile.svg";

const Home = lazy(() => import("pages/home"));
const SignUp = lazy(() => import("pages/signup"));
const SignIn = lazy(() => import("pages/signin"));
const NotFound = lazy(() => import("pages/notfound"));
const Dashboard = lazy(() => import("pages/dashboard/home"));
const Profile = lazy(() => import("pages/dashboard/profile"));
const ProfileEdit = lazy(() => import("pages/dashboard/profile_edit"));
const CostData = lazy(() => import("pages/dashboard/cost_data"));
const Farm = lazy(() => import("pages/dashboard/farm"));
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
    element: <SignUp />,
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
        element: <Farm />,
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
        icon: <ReactSVG src={iconEconomics} />,
        category: "parrent",
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
    ],
  },
];

export { routes };
