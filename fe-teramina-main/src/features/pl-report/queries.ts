import { useMutation, useQuery } from "@tanstack/react-query";
import { axios } from "helper/axios";

export const plReportKeys = {
  cycle: (cycle_id: string) => ["pl-report", cycle_id] as const,
  farm: (farm_id: string) => ["pl-report-farm", farm_id] as const,
  farmYear: (farm_id: string, year: number) => ["pl-report-farm-year", farm_id, year] as const,
  narrative: (cycle_id: string) => ["pl-report-narrative", cycle_id] as const,
};

export const usePLReport = (cycle_id: string) =>
  useQuery({
    queryKey: plReportKeys.cycle(cycle_id),
    queryFn: () =>
      axios.get("/cycle/report/pl", { params: { cycle_id } }).then((r: any) => r?.payload ?? null),
    enabled: !!cycle_id,
  });

export const useFarmPLReport = (farm_id: string) =>
  useQuery({
    queryKey: plReportKeys.farm(farm_id),
    queryFn: () =>
      axios.get("/farm/report/pl", { params: { farm_id } }).then((r: any) => r?.payload ?? null),
    enabled: !!farm_id,
  });

export const useFarmYearPLReport = (farm_id: string, year: number) =>
  useQuery({
    queryKey: plReportKeys.farmYear(farm_id, year),
    queryFn: () =>
      axios.get("/farm/report/pl/year", { params: { farm_id, year } }).then((r: any) => r?.payload ?? null),
    enabled: !!farm_id && !!year,
  });

export const usePLNarrative = (cycle_id: string, enabled: boolean) =>
  useQuery({
    queryKey: plReportKeys.narrative(cycle_id),
    queryFn: () =>
      axios.get("/cycle/report/pl/narrative", { params: { cycle_id } }).then((r: any) => r?.payload?.narrative ?? null),
    enabled: !!cycle_id && enabled,
    staleTime: 1000 * 60 * 10,
  });

export const useSharePLReport = (cycle_id: string) =>
  useMutation({
    mutationFn: () =>
      axios
        .post("/cycle/report/pl/share", null, { params: { cycle_id } })
        .then((r: any) => r?.payload ?? null),
  });

export const usePublicPLReport = (token: string) =>
  useQuery({
    queryKey: ["pl-report-share", token],
    queryFn: () =>
      axios.get(`/report/share/${token}`).then((r: any) => r?.payload ?? null),
    enabled: !!token,
    retry: false,
  });

export const downloadPLPdf = (cycle_id: string) =>
  axios
    .get("/cycle/report/pl/pdf", { params: { cycle_id }, responseType: "blob" })
    .then((blob: any) => {
      const url = URL.createObjectURL(blob as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pl_report_${cycle_id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    });

export const downloadPLExcel = (cycle_id: string) =>
  axios
    .get("/cycle/report/pl/excel", { params: { cycle_id }, responseType: "blob" })
    .then((blob: any) => {
      const url = URL.createObjectURL(blob as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pl_report_${cycle_id}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    });

export const downloadBankPdf = (cycle_id: string) =>
  axios
    .get("/cycle/report/pl/pdf/bank", { params: { cycle_id }, responseType: "blob" })
    .then((blob: any) => {
      const url = URL.createObjectURL(blob as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pl_bank_${cycle_id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    });
