import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import React, { createElement } from "react";
import { server } from "../mocks/server";
import { farmKeys, useFarmList } from "features/farm/queries";

// Pure key structure tests
describe("farmKeys", () => {
  it("has the correct list key", () => {
    expect(farmKeys.list).toEqual(["farms"]);
  });
});

// Integration test: hook fetches data via MSW-intercepted HTTP
describe("useFarmList", () => {
  const mockFarms = [
    { id: "1", name: "Farm Alpha" },
    { id: "2", name: "Farm Beta" },
  ];

  function wrapper({ children }: { children: React.ReactNode }) {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return createElement(QueryClientProvider, { client: queryClient }, children);
  }

  it("returns farm list from /farm/list-farm", async () => {
    server.use(
      http.get("*/farm/list-farm", () =>
        HttpResponse.json({ payload: mockFarms })
      )
    );

    const { result } = renderHook(() => useFarmList(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockFarms);
  });

  it("surfaces error when endpoint fails", async () => {
    server.use(
      http.get("*/farm/list-farm", () =>
        HttpResponse.json({ detail: "Server error" }, { status: 500 })
      )
    );

    const { result } = renderHook(() => useFarmList(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
