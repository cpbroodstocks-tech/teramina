import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import React, { createElement } from "react";
import { server } from "../mocks/server";
import { pondKeys, usePondList } from "features/pond/queries";

vi.mock("react-router-dom", async (importActual) => {
  const actual = await importActual<typeof import("react-router-dom")>();
  return { ...actual, useParams: () => ({ farm_id: "farm-1" }) };
});

describe("pondKeys", () => {
  it("has the correct list key structure", () => {
    const params = { farm_id: "farm-1" };
    expect(pondKeys.list(params)).toEqual(["ponds", params]);
  });
});

describe("usePondList", () => {
  const mockPonds = [
    { id: "1", name: "Pond A" },
    { id: "2", name: "Pond B" },
  ];

  function wrapper({ children }: { children: React.ReactNode }) {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return createElement(QueryClientProvider, { client: queryClient }, children);
  }

  it("returns pond list from /pond/list-pond", async () => {
    server.use(
      http.get("*/pond/list-pond", () =>
        HttpResponse.json({ payload: mockPonds })
      )
    );

    const { result } = renderHook(() => usePondList(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockPonds);
  });

  it("surfaces error when endpoint fails", async () => {
    server.use(
      http.get("*/pond/list-pond", () =>
        HttpResponse.json({ detail: "Server error" }, { status: 500 })
      )
    );

    const { result } = renderHook(() => usePondList(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
