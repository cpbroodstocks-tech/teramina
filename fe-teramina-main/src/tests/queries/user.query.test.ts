import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React, { createElement, useState } from "react";
import { userKeys, useUserProfile, useUpdateProfile, useUploadCostData } from "features/user/queries";

const mockAxios = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}));

vi.mock("helper/axios", () => ({
  axios: mockAxios,
}));

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("store/toast.store", () => {
  const setToast = vi.fn();
  return {
    useToastStore: Object.assign(() => ({ setToast }), { getState: () => ({ setToast }) }),
  };
});

beforeEach(() => {
  mockAxios.get.mockReset();
  mockAxios.post.mockReset();
});

function Wrapper({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  );
  return createElement(QueryClientProvider, { client: queryClient }, children);
}

// ── Key structure ─────────────────────────────────────────────────────────

describe("userKeys", () => {
  it("has correct profile key", () => {
    expect(userKeys.profile).toEqual(["user-profile"]);
  });
});

// ── useUserProfile ────────────────────────────────────────────────────────

describe("useUserProfile", () => {
  it("returns profile data from /user/get-profile", async () => {
    const profile = { id: "u1", name: "Alice", email: "alice@example.com" };
    mockAxios.get.mockResolvedValue({ payload: profile });

    const { result } = renderHook(() => useUserProfile(), { wrapper: Wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(profile);
    expect(mockAxios.get).toHaveBeenCalledWith("/user/get-profile");
  });

  it("surfaces error when endpoint fails", async () => {
    mockAxios.get.mockRejectedValue(new Error("Bad request"));

    const { result } = renderHook(() => useUserProfile(), { wrapper: Wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

// ── useUpdateProfile ──────────────────────────────────────────────────────

describe("useUpdateProfile", () => {
  it("POSTs multipart form data to /user/update-profile", async () => {
    let capturedContentType = "";
    mockAxios.post.mockImplementation((_url, _data, config) => {
      capturedContentType = config?.headers?.["Content-Type"] ?? "";
      return Promise.resolve({ payload: { name: "Bob Updated" } });
    });

    const { result } = renderHook(() => useUpdateProfile(), { wrapper: Wrapper });
    const formData = new FormData();
    formData.append("name", "Bob Updated");
    result.current.mutate(formData);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(capturedContentType).toMatch(/multipart\/form-data/);
    expect(mockAxios.post).toHaveBeenCalledWith(
      "/user/update-profile",
      formData,
      expect.objectContaining({ headers: expect.objectContaining({ "Content-Type": "multipart/form-data" }) })
    );
  });

  it("surfaces error when update fails", async () => {
    mockAxios.post.mockRejectedValue(new Error("Bad request"));

    const { result } = renderHook(() => useUpdateProfile(), { wrapper: Wrapper });
    result.current.mutate(new FormData());

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

// ── useUploadCostData ─────────────────────────────────────────────────────

describe("useUploadCostData", () => {
  it("POSTs file to /cost/add-single-cost-data with correct params", async () => {
    mockAxios.post.mockResolvedValue({ payload: {} });

    const { result } = renderHook(() => useUploadCostData(), { wrapper: Wrapper });
    // Use Blob (not File) to avoid slow File serialization in Node.js/jsdom
    const file = new Blob(["cost data"], { type: "text/csv" }) as unknown as File;
    result.current.mutate({
      farm_id: "farm-1",
      start_date: "2024-01-01",
      end_date: "2024-01-31",
      file,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 5000 });
    expect(mockAxios.post).toHaveBeenCalledWith(
      "/cost/add-single-cost-data",
      expect.any(FormData),
      expect.objectContaining({
        params: {
          farm_id: "farm-1",
          start_date: "2024-01-01",
          end_date: "2024-01-31",
        },
        headers: { "Content-Type": "multipart/form-data" },
      })
    );
  });

  it("surfaces error when upload fails", async () => {
    mockAxios.post.mockRejectedValue(new Error("Invalid file"));

    const { result } = renderHook(() => useUploadCostData(), { wrapper: Wrapper });
    const file = new Blob(["bad data"], { type: "text/plain" }) as unknown as File;
    result.current.mutate({ farm_id: "f1", start_date: "2024-01-01", end_date: "2024-01-31", file });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
  });
});
