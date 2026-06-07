import { fetchDashboardFilter, fetchFilterUrl, fetchWaterQualityFilter } from "features/filter/queries";
import { getDashboardContext, useDashboardContextStore } from "store/dashboard-context.store";

type Option = { id: string; name: string };

const choose = (items: Option[], preferred: string) =>
  items.find((item) => item.id === preferred) || items[0] || null;

export const persistDashboardSelection = (
  key: "farm_id" | "pond_id" | "cycle_id",
  value: string,
  options: { farms?: Option[]; ponds?: Option[]; cycles?: Option[] }
) => {
  const setContext = useDashboardContextStore.getState().setContext;
  if (key === "farm_id") {
    const farm = options.farms?.find((item) => item.id === value);
    setContext({ farm_id: value, farm_name: farm?.name || "", pond_id: "", pond_name: "", cycle_id: "", cycle_name: "" });
  } else if (key === "pond_id") {
    const pond = options.ponds?.find((item) => item.id === value);
    setContext({ pond_id: value, pond_name: pond?.name || "", cycle_id: "", cycle_name: "" });
  } else {
    const cycle = options.cycles?.find((item) => item.id === value);
    setContext({ cycle_id: value, cycle_name: cycle?.name || "" });
  }
};

export const loadSharedFilterContext = async ({
  filterType = "historical",
  waterQuality = false,
}: {
  filterType?: "historical" | "forecast";
  waterQuality?: boolean;
}) => {
  const current = getDashboardContext();
  const root: any = waterQuality ? await fetchWaterQualityFilter() : await fetchDashboardFilter();
  const farms: Option[] = root?.payload || [];
  const farm = choose(farms, current.farm_id);
  if (!farm) return { values: null, filter: { farms, ponds: [], cycles: [] } };

  const base = waterQuality ? "/dashboard/wq-filter" : "/dashboard/filter";
  const pondsResponse: any = await fetchFilterUrl(`${base}?farm_id=${farm.id}${waterQuality ? "" : `&filter_type=${filterType}`}`);
  const ponds: Option[] = pondsResponse?.payload || [];
  const pond = choose(ponds, current.pond_id);
  if (!pond) return { values: null, filter: { farms, ponds, cycles: [] } };

  const cyclesResponse: any = await fetchFilterUrl(
    `${base}?farm_id=${farm.id}&pond_id=${pond.id}${waterQuality ? "" : `&filter_type=${filterType}`}`
  );
  const cycles: Option[] = cyclesResponse?.payload || [];
  const cycle = choose(cycles, current.cycle_id);
  if (!cycle) return { values: null, filter: { farms, ponds, cycles } };

  const metadataResponse: any = await fetchFilterUrl(
    `${base}?farm_id=${farm.id}&pond_id=${pond.id}&cycle_id=${cycle.id}${waterQuality ? "" : `&filter_type=${filterType}`}`
  );
  const metadata = waterQuality ? metadataResponse?.payload?.[0]?.data : metadataResponse?.payload?.[0]?.daterange;
  useDashboardContextStore.getState().setContext({
    farm_id: farm.id,
    farm_name: farm.name,
    pond_id: pond.id,
    pond_name: pond.name,
    cycle_id: cycle.id,
    cycle_name: cycle.name,
  });

  return {
    values: { farm_id: farm.id, pond_id: pond.id, cycle_id: cycle.id },
    filter: {
      farms,
      ponds,
      cycles,
      daterange: waterQuality && metadata
        ? { start_date: metadata.start_date, end_date: metadata.end_date }
        : metadata,
      variables: waterQuality ? metadata?.variables || [] : undefined,
    },
  };
};
