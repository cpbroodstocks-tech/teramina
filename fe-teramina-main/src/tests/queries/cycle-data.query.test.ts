import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import React, { createElement } from "react";
import { server } from "../mocks/server";
import { cycleDataKeys, useCycleDataList } from "features/cycle-data/queries";

vi.mock("react-router-dom", async (importActual) => {
  const actual = await importActual<typeof import("react-router-dom")>();
  return { ...actual, useParams: () => ({ farm_id: "farm-1", pond_id: "pond-1", cycle_id: "cycle-1" }) };
});

describe("cycleDataKeys", () => {
  it("has the correct list key structure", () => {
    const params = { farm_id: "farm-1", pond_id: "pond-1", cycle_id: "cycle-1" };
    expect(cycleDataKeys.list(params)).toEqual(["cycle-data", params]);
  });
});

describe("useCycleDataList", () => {
  const mockCycleData = [
    { id: "1", doc: 1, abw: 0.5 },
    { id: "2", doc: 2, abw: 0.8 },
  ];

  function wrapper({ children }: { children: React.ReactNode }) {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return createElement(QueryClientProvider, { client: queryClient }, children);
  }

  it("returns cycle data list from /cycle-data/list-cycle-data", async () => {
    server.use(
      http.get("*/cycle-data/list-cycle-data", () =>
        HttpResponse.json({ payload: mockCycleData })
      )
    );

    const { result } = renderHook(() => useCycleDataList(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockCycleData);
  });

  it("surfaces error when endpoint fails", async () => {
    server.use(
      http.get("*/cycle-data/list-cycle-data", () =>
        HttpResponse.json({ detail: "Server error" }, { status: 500 })
      )
    );

    const { result } = renderHook(() => useCycleDataList(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
