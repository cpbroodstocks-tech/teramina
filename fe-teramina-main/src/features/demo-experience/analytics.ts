import ReactGA from "react-ga4";
import { axios } from "helper/axios";

const allowedPropertyKeys = new Set(["route", "scenario", "step"]);

export const trackDemoEvent = async (eventName: string, properties: Record<string, string> = {}) => {
  const cleanProperties = Object.fromEntries(
    Object.entries(properties).filter(([key, value]) => allowedPropertyKeys.has(key) && typeof value === "string")
  );
  const result = await axios.post("/user/demo-experience/events", {
    event_name: eventName,
    properties: cleanProperties,
  }).then((response: any) => response?.payload);

  if ((import.meta as any).env?.VITE_GA_MEASUREMENT_ID) {
    ReactGA.event(eventName, cleanProperties);
  }
  return result;
};
