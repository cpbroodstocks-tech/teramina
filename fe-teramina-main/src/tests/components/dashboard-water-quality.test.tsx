import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import WaterQuality from "features/dashboard/water-quality";

const waterQualityHooks = vi.hoisted(() => ({
  useFilter: vi.fn(),
  useWaterQualityDashboard: vi.fn(),
}));

vi.mock("features/filter/water-quality/hooks", () => ({
  useFilter: waterQualityHooks.useFilter,
}));

vi.mock("widgets/water-quality/queries", () => ({
  useWaterQualityDashboard: waterQualityHooks.useWaterQualityDashboard,
}));

vi.mock("features/filter/water-quality/components/datepicker-popup", () => ({
  StartDatePickerPopUp: () => <div>Start date</div>,
  EndDatePickerPopUp: () => <div>End date</div>,
}));

vi.mock("components/echarts/line", () => ({
  default: () => <div>Line chart</div>,
}));

vi.mock("components/echarts/scatter", () => ({
  default: () => <div>Scatter chart</div>,
}));

vi.mock("features/filter/harvest/styles", () => ({
  useStyles: () => ({ classes: {} }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

describe("Water Quality dashboard", () => {
  beforeEach(() => {
    waterQualityHooks.useFilter.mockReturnValue({
      loading: false,
      filter: {
        farms: [],
        ponds: [],
        cycles: [],
        daterange: {},
        variables: [],
      },
      form: {
        values: {
          farm_id: "",
          pond_id: "",
          cycle_id: [],
          variables: [],
          start_date: "",
          end_date: "",
        },
        handleSubmit: vi.fn(),
        handleReset: vi.fn(),
        dirty: false,
      },
      onFilterChange: vi.fn(),
      submittedParams: {},
    });
  });

  it("does not crash when form errors are absent", () => {
    waterQualityHooks.useWaterQualityDashboard.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    });

    render(<WaterQuality />);

    expect(screen.getByRole("button", { name: "APPLY_FILTER" })).toBeDisabled();
  });

  it("does not crash when the table data is empty", async () => {
    waterQualityHooks.useWaterQualityDashboard.mockReturnValue({
      data: { line_plot: [], scatter_plot: [], data: [] },
      isLoading: false,
      isError: false,
    });

    render(<WaterQuality />);
    await userEvent.click(screen.getByRole("tab", { name: "TABLE" }));

    expect(screen.getByRole("table")).toBeInTheDocument();
  });
});
