import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import React, { createElement } from "react";
import { server } from "../mocks/server";
import {
  benchmarkKeys,
  useBenchmarkPerformance,
  useOptInBenchmark,
  useOptOutBenchmark,
  useFeedingRecommendation,
  useOverrideFeedingRecommendation,
  useGenerateInsight,
  useLoadCachedInsight,
  usePopulateCycleData,
  useDownloadCycleData,
} from "features/cycle-detail/queries";
import { axios } from "helper/axios";

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

const CYCLE_ID = "cycle-detail-q-001";

afterEach(() => {
  vi.restoreAllMocks();
});

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return createElement(QueryClientProvider, { client: queryClient }, children);
}

// ── Key structure ─────────────────────────────────────────────────────────

describe("benchmarkKeys", () => {
  it("has correct performance key structure", () => {
    expect(benchmarkKeys.performance(CYCLE_ID)).toEqual(["benchmark", CYCLE_ID]);
  });
});

// ── Benchmark queries ─────────────────────────────────────────────────────

describe("useBenchmarkPerformance", () => {
  it("fetches performance data from /benchmark/my-performance", async () => {
    const data = { opted_in: true, performance: { metrics: {} } };
    server.use(
      http.get("*/benchmark/my-performance", () => HttpResponse.json({ payload: data }))
    );

    const { result } = renderHook(() => useBenchmarkPerformance(CYCLE_ID), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(data);
  });

  it("returns null when endpoint returns no payload", async () => {
    server.use(
      http.get("*/benchmark/my-performance", () => HttpResponse.json({}))
    );

    const { result } = renderHook(() => useBenchmarkPerformance(CYCLE_ID), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeNull();
  });
});

describe("useOptInBenchmark", () => {
  it("POSTs to /benchmark/opt-in with cycle_id", async () => {
    let capturedBody: Record<string, string> = {};
    server.use(
      http.get("*/benchmark/my-performance", () => HttpResponse.json({ payload: {} })),
      http.post("*/benchmark/opt-in", async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, string>;
        return HttpResponse.json({ payload: {} });
      })
    );

    const { result } = renderHook(() => useOptInBenchmark(CYCLE_ID), { wrapper });
    result.current.mutate(undefined);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(capturedBody.cycle_id).toBe(CYCLE_ID);
  });
});

describe("useOptOutBenchmark", () => {
  it("POSTs to /benchmark/opt-out with cycle_id", async () => {
    let capturedBody: Record<string, string> = {};
    server.use(
      http.get("*/benchmark/my-performance", () => HttpResponse.json({ payload: {} })),
      http.post("*/benchmark/opt-out", async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, string>;
        return HttpResponse.json({ payload: {} });
      })
    );

    const { result } = renderHook(() => useOptOutBenchmark(CYCLE_ID), { wrapper });
    result.current.mutate(undefined);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(capturedBody.cycle_id).toBe(CYCLE_ID);
  });
});

// ── Feeding recommendation queries ────────────────────────────────────────

describe("useFeedingRecommendation", () => {
  it("fetches recommendation from /feeding/recommendation", async () => {
    const rec = { recommended_ration_kg: 15, doc: 30, model_layer: "base" };
    server.use(
      http.get("*/feeding/recommendation", () => HttpResponse.json({ payload: rec }))
    );

    const { result } = renderHook(() => useFeedingRecommendation(CYCLE_ID), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(rec);
  });

  it("returns null when no payload", async () => {
    server.use(
      http.get("*/feeding/recommendation", () => HttpResponse.json({}))
    );

    const { result } = renderHook(() => useFeedingRecommendation(CYCLE_ID), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeNull();
  });
});

describe("useOverrideFeedingRecommendation", () => {
  it("POSTs override data with correct params", async () => {
    let capturedUrl = "";
    let capturedBody: Record<string, unknown> = {};
    server.use(
      http.post("*/feeding/recommendation/override", async ({ request }) => {
        capturedUrl = request.url;
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ payload: {} });
      })
    );

    const { result } = renderHook(() => useOverrideFeedingRecommendation(CYCLE_ID), { wrapper });
    result.current.mutate({ doc: 45, actual_kg: 12, override_reason: "test reason" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(capturedUrl).toContain(`cycle_id=${CYCLE_ID}`);
    expect(capturedUrl).toContain("doc=45");
    expect(capturedBody.actual_kg).toBe(12);
    expect(capturedBody.override_reason).toBe("test reason");
  });
});

// ── AI Insight queries ────────────────────────────────────────────────────

describe("useGenerateInsight", () => {
  it("GETs insight from /summarize/insight and returns insight object", async () => {
    const insight = { summary: "Good results", performance_score: 78 };
    server.use(
      http.get("*/summarize/insight", () =>
        HttpResponse.json({ payload: { insight } })
      )
    );

    const { result } = renderHook(() => useGenerateInsight(), { wrapper });
    result.current.mutate({ cycle_id: CYCLE_ID, type: "performance" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(insight);
  });

  it("returns null when no insight in payload", async () => {
    server.use(
      http.get("*/summarize/insight", () => HttpResponse.json({ payload: {} }))
    );

    const { result } = renderHook(() => useGenerateInsight(), { wrapper });
    result.current.mutate({ cycle_id: CYCLE_ID, type: "feeding" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeNull();
  });
});

describe("useLoadCachedInsight", () => {
  it("GETs cached insight from /summarize/insight/cached", async () => {
    const insight = { summary: "Cached insight", performance_score: 65 };
    server.use(
      http.get("*/summarize/insight/cached", () =>
        HttpResponse.json({ payload: { insight } })
      )
    );

    const { result } = renderHook(() => useLoadCachedInsight(), { wrapper });
    result.current.mutate({ cycle_id: CYCLE_ID, type: "weekly" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(insight);
  });
});

// ── Populate / download ───────────────────────────────────────────────────

describe("usePopulateCycleData", () => {
  it("POSTs file as multipart/form-data to populate-cycle-data", async () => {
    const postSpy = vi.spyOn(axios, "post").mockResolvedValue({ payload: { rows_inserted: 100 } });

    const { result } = renderHook(() => usePopulateCycleData(CYCLE_ID), { wrapper });
    const file = new Blob(["a,b\n1,2"], { type: "text/csv" }) as unknown as File;
    result.current.mutate({ file, source_type: "csv" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(postSpy).toHaveBeenCalledWith(
      `/cycle-data/populate-cycle-data?cycle_id=${CYCLE_ID}&source_type=csv`,
      expect.any(FormData),
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } })
    );
  });
});

describe("useDownloadCycleData", () => {
  it("GETs blob from download-cycle_data", async () => {
    server.use(
      http.get("*/cycle-data/download-cycle_data", () =>
        HttpResponse.arrayBuffer(new ArrayBuffer(4))
      )
    );

    const { result } = renderHook(() => useDownloadCycleData(CYCLE_ID), { wrapper });
    result.current.mutate(undefined);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});
