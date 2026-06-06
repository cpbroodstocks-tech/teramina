import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useFilter } from "features/filter/overview/hooks";

const filterQueries = vi.hoisted(() => ({
  fetchDashboardFilter: vi.fn(),
  fetchFilteredData: vi.fn(),
  fetchFilterUrl: vi.fn(),
}));

vi.mock("features/filter/queries", () => filterQueries);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: vi.fn() }),
}));

describe("Overview filter", () => {
  beforeEach(() => {
    filterQueries.fetchDashboardFilter.mockReset();
    filterQueries.fetchFilteredData.mockReset();
    filterQueries.fetchFilterUrl.mockReset();
    filterQueries.fetchDashboardFilter.mockResolvedValue({ payload: [] });
    filterQueries.fetchFilteredData.mockResolvedValue({ payload: { ready: true } });
  });

  it("requests the overview endpoint when Apply Filter submits", async () => {
    const { result } = renderHook(() => useFilter("/dashboard/overview"));

    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.form.setFieldValue("farm_id", "farm-1", { shouldDirty: true });
    });

    await act(async () => {
      await result.current.form.handleSubmit();
    });

    await waitFor(() =>
      expect(filterQueries.fetchFilteredData).toHaveBeenCalledWith("/dashboard/overview", {
        farm_id: "farm-1",
        pond_id: "",
        cycle_id: "",
        date: "",
      })
    );
    expect(result.current.data).toEqual({ ready: true });
  });
});
