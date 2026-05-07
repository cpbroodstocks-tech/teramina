import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import React, { createElement } from "react";
import { server } from "../mocks/server";
import { cycleKeys, useCycleList } from "features/cycle/queries";

vi.mock("react-router-dom", async (importActual) => {
  const actual = await importActual<typeof import("react-router-dom")>();
  return { ...actual, useParams: () => ({ farm_id: "farm-1", pond_id: "pond-1" }) };
});

describe("cycleKeys", () => {
  it("has the correct list key structure", () => {
    const params = { farm_id: "farm-1", pond_id: "pond-1" };
    expect(cycleKeys.list(params)).toEqual(["cycles", params]);
  });
});

describe("useCycleList", () => {
  const mockCycles = [
    { id: "1", name: "Cycle 1" },
    { id: "2", name: "Cycle 2" },
  ];

  function wrapper({ children }: { children: React.ReactNode }) {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return createElement(QueryClientProvider, { client: queryClient }, children);
  }

  it("returns cycle list from /cycle/list-cycles", async () => {
    server.use(
      http.get("*/cycle/list-cycles", () =>
        HttpResponse.json({ payload: mockCycles })
      )
    );

    const { result } = renderHook(() => useCycleList(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockCycles);
  });

  it("surfaces error when endpoint fails", async () => {
    server.use(
      http.get("*/cycle/list-cycles", () =>
        HttpResponse.json({ detail: "Server error" }, { status: 500 })
      )
    );

    const { result } = renderHook(() => useCycleList(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
