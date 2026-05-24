const CONTEXT_KEYS = ["farm_id", "pond_id", "cycle_id"];

const getStorageValue = (storage, key) => {
  try {
    return storage?.getItem(key) || "";
  } catch {
    return "";
  }
};

export const inferAgentPageType = (pathname = "") => {
  if (pathname.includes("pond-timeline")) return "pond_timeline";
  if (pathname.includes("harvest-simulator")) return "harvest_simulator";
  if (pathname.includes("dashboard")) return "dashboard";
  if (pathname.includes("cycle")) return "cycle";
  if (pathname.includes("pond")) return "pond";
  if (pathname.includes("farm")) return "farm";
  return "unknown";
};

export const buildAgentContext = ({
  params = {},
  search = "",
  pathname = "",
  storage = typeof window === "undefined" ? null : window.localStorage,
} = {}) => {
  const query = new URLSearchParams(search || "");
  const getContextValue = (key) => params[key] || query.get(key) || getStorageValue(storage, key);
  const farmId = getContextValue("farm_id");
  const pondId = getContextValue("pond_id");
  const cycleId = getContextValue("cycle_id");
  const filters = {};

  query.forEach((value, key) => {
    if (!CONTEXT_KEYS.includes(key)) filters[key] = value;
  });

  return {
    farm_id: farmId,
    pond_id: pondId,
    cycle_id: cycleId,
    page_context: {
      route: pathname,
      page_type: inferAgentPageType(pathname),
      farm_id: farmId,
      pond_id: pondId,
      cycle_id: cycleId,
      filters,
    },
  };
};
