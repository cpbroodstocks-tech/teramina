import { axios } from "helper/axios";

export const fetchFilterUrl = (url: string) => axios.get(url);

export const fetchFilteredData = (api: string, values: Record<string, string>) =>
  axios.get(`${api}?${new URLSearchParams(values).toString()}`);

export const fetchDashboardFilter = () => axios.get("/dashboard/filter");

export const fetchWaterQualityFilter = () => axios.get("/dashboard/wq-filter");
