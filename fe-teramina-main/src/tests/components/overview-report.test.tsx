import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@mui/material/styles";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { theme } from "theme";
import Overview from "widgets/overview";

// ── Mocks ──────────────────────────────────────────────────────────────────

const mockAxios = vi.hoisted(() => ({
  post: vi.fn(),
  get: vi.fn(),
}));

vi.mock("helper/axios", () => ({
  axios: mockAxios,
}));

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("react-svg", () => ({
  ReactSVG: () => <span data-testid="svg-icon" />,
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

const mockSetToast = vi.fn();
vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: mockSetToast }),
}));

vi.mock("hooks/useUserCheckData", () => ({
  useUserCheckData: () => ({ loading: false, data: true, error: false }),
}));

// Mock the Markdown AI-summary component (calls external API, not relevant here)
vi.mock("components/markdown", () => ({
  Markdown: () => null,
}));

// Mock echarts components to avoid canvas/SVG rendering issues in jsdom
vi.mock("components/echarts/line", () => ({
  default: () => <div data-testid="line-chart" />,
}));

vi.mock("components/echarts/scatter", () => ({
  default: () => <div data-testid="scatter-chart" />,
}));

// Mock farm stepper (shown when data=false, not needed here)
vi.mock("features/farm/stepper", () => ({
  default: () => <div>Stepper</div>,
}));

// Mock the filter hook so we don't need real API calls for filter setup
const mockOverviewData = {
  pond_info: {
    title: "Pond Info",
    data: [
      { title: "DOC", value: 30, unit: "days" },
    ],
  },
  performance: {
    title: "Performance",
    data: [1, 2, 3, 4, 5].map((i) => ({
      title: `Metric ${i}`,
      value: i * 10,
      unit: "kg",
      description: `Description ${i}`,
      change_ratio: i,
      current_status: i % 2 === 0 ? "increase" : "stable",
    })),
    plot: [
      {
        title: "ABW Plot",
        echart_option: {
          legend: { data: [], show: false },
          xAxis: { data: ["2024-01-01"] },
          yAxis: {},
          series: [],
        },
      },
      {
        title: "SGR Plot",
        echart_option: {
          legend: { data: [], show: false },
          xAxis: { data: ["2024-01-01"] },
          yAxis: {},
          series: [],
        },
      },
    ],
  },
  economics: {
    data: [
      { title: "Total Cost", value: "Rp 1.000.000" },
      { title: "Total Revenue", value: "Rp 2.000.000" },
    ],
  },
  prompt_summary: "Summarize this farm data.",
};

vi.mock("features/filter/overview/hooks", () => ({
  useFilter: () => ({
    loading: false,
    error: false,
    filter: {
      farms: [{ _id: "f1", name: "Farm 1" }],
      ponds: [],
      cycles: [],
      daterange: { start_date: "01/01/2024", end_date: "04/30/2024" },
    },
    data: mockOverviewData,
    form: {
      values: { farm_id: "f1", pond_id: "p1", cycle_id: "c1", date: "" },
      handleSubmit: () => {},
      handleReset: () => {},
      dirty: false,
      setFieldValue: () => {},
    },
    appliedValues: { farm_id: "f1", pond_id: "p1", cycle_id: "c1", date: "" },
    onFilterChange: () => {},
  }),
}));

// Mock the Filter (overview filter bar) to avoid its internal API calls
vi.mock("features/filter/overview", () => ({
  default: () => <div data-testid="filter-bar" />,
}));

// ── Helpers ────────────────────────────────────────────────────────────────

function renderComponent() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <MemoryRouter>
          <Overview />
        </MemoryRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

function jsonBlob(payload: unknown) {
  return {
    type: "application/json",
    text: vi.fn().mockResolvedValue(JSON.stringify(payload)),
  } as unknown as Blob;
}

function pdfBlob() {
  return {
    type: "application/pdf",
  } as unknown as Blob;
}

// ── Suite ──────────────────────────────────────────────────────────────────

describe("Overview — Report button", () => {
  beforeEach(() => {
    mockAxios.post.mockReset();
    mockAxios.get.mockReset();
    mockAxios.post.mockResolvedValue({ task_id: "task-123" });
    mockAxios.get.mockResolvedValue(jsonBlob({ status: "pending" }));
    mockSetToast.mockClear();
    // Ensure localStorage values are set so the mutationFn can read them
    localStorage.setItem("farm_id", "f1");
    localStorage.setItem("pond_id", "p1");
    localStorage.setItem("cycle_id", "c1");
    localStorage.setItem("date", "");
    localStorage.setItem("authentication", "test-token");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
    if (vi.isFakeTimers()) vi.useRealTimers();
    localStorage.clear();
  });

  it("Report button is visible when data is loaded", async () => {
    renderComponent();
    expect(await screen.findByRole("button", { name: /Report/i })).toBeInTheDocument();
  });

  it("clicking Report button opens info dialog with progress message", async () => {
    const user = userEvent.setup();

    renderComponent();
    const reportBtn = await screen.findByRole("button", { name: /Report/i });
    await user.click(reportBtn);

    expect(
      await screen.findByText("Report download in progress. This may take up to 1 minute...")
    ).toBeInTheDocument();
  });

  it("POST /create-report → poll returns PDF blob → download triggered → dialog closes", async () => {
    const mockCreateObjectURL = vi.fn(() => "blob:mock-url");
    const mockRevokeObjectURL = vi.fn();
    Object.defineProperty(window.URL, "createObjectURL", {
      writable: true,
      value: mockCreateObjectURL,
    });
    Object.defineProperty(window.URL, "revokeObjectURL", {
      writable: true,
      value: mockRevokeObjectURL,
    });

    const mockLinkClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    mockAxios.get.mockResolvedValue(pdfBlob());

    const user = userEvent.setup();
    renderComponent();

    const reportBtn = await screen.findByRole("button", { name: /Report/i });
    await user.click(reportBtn);

    // Dialog opens
    expect(
      await screen.findByText("Report download in progress. This may take up to 1 minute...")
    ).toBeInTheDocument();

    // Wait for the polling to resolve and the PDF download to be triggered
    await waitFor(() => expect(mockLinkClick).toHaveBeenCalled(), { timeout: 15000 });
    expect(mockCreateObjectURL).toHaveBeenCalled();

    // Dialog should close after download
    await waitFor(() =>
      expect(
        screen.getByText("Report download in progress. This may take up to 1 minute...")
      ).not.toBeVisible()
    );

    mockLinkClick.mockRestore();
  }, 20000);

  it("poll returns FAILURE status → error toast shown → dialog closes", async () => {
    const user = userEvent.setup();
    mockAxios.post.mockResolvedValue({ task_id: "task-456" });
    mockAxios.get.mockResolvedValue(jsonBlob({ status: "FAILURE" }));

    renderComponent();
    const reportBtn = await screen.findByRole("button", { name: /Report/i });
    await user.click(reportBtn);

    // Dialog opens
    expect(
      await screen.findByText("Report download in progress. This may take up to 1 minute...")
    ).toBeInTheDocument();

    // Wait for failure toast
    await waitFor(
      () =>
        expect(mockSetToast).toHaveBeenCalledWith(
          expect.objectContaining({
            variant: "error",
            text: "Report generation failed. Please try again.",
          })
        ),
      { timeout: 15000 }
    );

    // Dialog closes on failure
    await waitFor(() =>
      expect(
        screen.getByText("Report download in progress. This may take up to 1 minute...")
      ).not.toBeVisible()
    );
  }, 20000);
});
