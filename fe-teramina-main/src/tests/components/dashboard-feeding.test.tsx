import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Feeding from "features/dashboard/feeding";

const feedingHooks = vi.hoisted(() => ({
  useFilter: vi.fn(),
  useFeedingDashboard: vi.fn(),
}));

vi.mock("features/filter/feeding/hooks", () => ({
  useFilter: feedingHooks.useFilter,
}));

vi.mock("widgets/feeding/queries", () => ({
  useFeedingDashboard: feedingHooks.useFeedingDashboard,
}));

vi.mock("features/filter/default", () => ({
  default: () => <div>Filter</div>,
}));

vi.mock("features/feeding/modal-add-feeding", () => ({
  default: () => <button type="button">Add feeding</button>,
}));

vi.mock("components/echarts/line", () => ({
  default: () => <div>Feed chart</div>,
}));

vi.mock("hooks/useLineEchartsGenerateOptions", () => ({
  useLineEchartsGenerateOptions: () => ({
    generateOptionsDefault: vi.fn(() => ({})),
  }),
}));

vi.mock("widgets/feeding/styles", () => ({
  useStyles: () => ({ classes: {} }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

describe("Feeding dashboard", () => {
  beforeEach(() => {
    feedingHooks.useFilter.mockReturnValue({
      loading: false,
      filter: {},
      form: {},
      selectedFilter: {},
      onFilterChange: vi.fn(),
      submittedParams: {},
    });
  });

  it("does not crash when daily adjustment entries are missing", () => {
    feedingHooks.useFeedingDashboard.mockReturnValue({
      data: {
        feed_status: { title: "Feeding Status", data: [] },
        feed_adjustment: { title: "Original Feeding Rate", data: [], plot: {} },
        daily_feed_adjustment: { title: "Daily Feeding Adjustment", data: [] },
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<Feeding />);

    expect(screen.getByText("Daily Feeding Adjustment")).toBeInTheDocument();
    expect(screen.getByText("Realization")).toBeInTheDocument();
  });
});
