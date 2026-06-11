import { beforeEach, describe, expect, it } from "vitest";
import { persistDashboardSelection } from "features/filter/shared-context";
import { getDashboardContext, useDashboardContextStore } from "store/dashboard-context.store";

describe("Dashboard context store", () => {
  beforeEach(() => {
    localStorage.clear();
    useDashboardContextStore.getState().clearContext();
  });

  it("reads selections written by pages that still use localStorage directly", () => {
    localStorage.setItem("farm_id", "farm-external");
    localStorage.setItem("pond_id", "pond-external");
    localStorage.setItem("cycle_id", "cycle-external");

    expect(getDashboardContext()).toMatchObject({
      farm_id: "farm-external",
      pond_id: "pond-external",
      cycle_id: "cycle-external",
    });
  });

  it("clears dependent selections when the shared farm changes", () => {
    useDashboardContextStore.getState().setContext({
      farm_id: "farm-old",
      pond_id: "pond-old",
      cycle_id: "cycle-old",
    });

    persistDashboardSelection("farm_id", "farm-new", {
      farms: [{ id: "farm-new", name: "New Farm" }],
    });

    expect(getDashboardContext()).toEqual({
      farm_id: "farm-new",
      farm_name: "New Farm",
      pond_id: "",
      pond_name: "",
      cycle_id: "",
      cycle_name: "",
    });
  });

  it("uses dashboard query parameters as the canonical context", () => {
    window.history.replaceState({}, "", "/dashboard?farm_id=farm-url&pond_id=pond-url&cycle_id=cycle-url");
    localStorage.setItem("farm_id", "farm-local");

    expect(getDashboardContext()).toMatchObject({
      farm_id: "farm-url",
      pond_id: "pond-url",
      cycle_id: "cycle-url",
    });
  });
});
