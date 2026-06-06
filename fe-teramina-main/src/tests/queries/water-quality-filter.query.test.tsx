import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useFilter } from "features/filter/water-quality/hooks";

const filterQueries = vi.hoisted(() => ({
  fetchFilterUrl: vi.fn(),
  fetchWaterQualityFilter: vi.fn(),
}));

vi.mock("features/filter/queries", () => filterQueries);

describe("Water Quality filter", () => {
  beforeEach(() => {
    filterQueries.fetchFilterUrl.mockReset();
    filterQueries.fetchWaterQualityFilter.mockReset();
    filterQueries.fetchWaterQualityFilter.mockResolvedValue({ payload: [] });
  });

  it("does not crash when a cycle metadata response is empty", async () => {
    filterQueries.fetchFilterUrl.mockResolvedValue({ payload: [] });
    const { result } = renderHook(() => useFilter());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.onFilterChange("cycle_id", ["cycle-1"]);
    });

    expect(result.current.filter.variables).toEqual([]);
  });

  it("only sends farm, pond, and cycle values to the filter endpoint", async () => {
    filterQueries.fetchFilterUrl
      .mockResolvedValueOnce({ payload: [{ id: "pond-1", name: "Pond 1" }] })
      .mockResolvedValueOnce({ payload: [{ id: "cycle-1", name: "Cycle 1" }] })
      .mockResolvedValueOnce({
        payload: [{
          data: {
            start_date: "2024-03-01",
            end_date: "2024-06-28",
            variables: ["do_avg", "wqi_1"],
          },
        }],
      });
    const { result } = renderHook(() => useFilter());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.onFilterChange("farm_id", "farm-1");
      await result.current.onFilterChange("pond_id", "pond-1");
      await result.current.onFilterChange("cycle_id", ["cycle-1"]);
    });

    expect(filterQueries.fetchFilterUrl).toHaveBeenLastCalledWith(
      "/dashboard/wq-filter?farm_id=farm-1&pond_id=pond-1&cycle_id=cycle-1"
    );
    expect(result.current.filter.variables).toEqual(["do_avg", "wqi_1"]);
  });
});
