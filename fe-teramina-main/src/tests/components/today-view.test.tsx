import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { server } from "../mocks/server";
import TodayView from "pages/dashboard/today";
import { useDashboardContextStore } from "store/dashboard-context.store";

const mockSetToast = vi.fn();
vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: mockSetToast }),
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => vi.fn() };
});

const todayPayload = {
  payload: {
    farm_name: "Test Farm",
    farm_id: "farm-1",
    as_of: "2026-01-01T00:00:00",
    alerts: [
      {
        id: "alert-1",
        alert_type: "water_quality",
        severity: "critical",
        message: "DO is critically low: 1.8 mg/L",
        cycle_id: "cycle-1",
        created_at: "2026-01-01T06:00:00",
      },
      {
        id: "alert-2",
        alert_type: "growth",
        severity: "warning",
        message: "SGR below threshold",
        cycle_id: "cycle-1",
        created_at: "2026-01-01T06:00:00",
      },
    ],
    ponds: [
      {
        pond_id: "pond-1",
        pond_name: "Pond Alpha",
        active_cycle_id: "cycle-1",
        current_doc: 35,
        do_avg: 3.1,
        temp_avg: 28.5,
        nh3: 0.01,
        abw_g: 12.4,
        do_status: "warning",
        nh3_status: "ok",
      },
    ],
    tasks: [
      {
        id: "task-1",
        task_type: "check",
        title: "Check aeration on Pond Alpha",
        description: "",
        pond_id: "pond-1",
        due_at: new Date(Date.now() - 3600000).toISOString(),
        is_overdue: true,
      },
    ],
    control_loops: [],
  },
};

function renderComponent() {
  useDashboardContextStore.getState().setContext({ farm_id: "farm-1" });
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <TodayView />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("TodayView", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
    useDashboardContextStore.getState().setContext({ farm_id: "farm-1" });
  });

  it("renders pond name and DO chip in the pond grid", async () => {
    server.use(
      http.get("*/agent/today", () => HttpResponse.json(todayPayload))
    );

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("Pond Alpha")).toBeInTheDocument();
    });
    expect(screen.getByText("3.1 mg/L")).toBeInTheDocument();
    expect(screen.getByText("DOC 35")).toBeInTheDocument();
  });

  it("renders critical alert in Urgent Actions section", async () => {
    server.use(
      http.get("*/agent/today", () => HttpResponse.json(todayPayload))
    );

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("Urgent Actions")).toBeInTheDocument();
    });
    expect(screen.getByText("DO is critically low: 1.8 mg/L")).toBeInTheDocument();
  });

  it("renders warning alert in Active Alerts section", async () => {
    server.use(
      http.get("*/agent/today", () => HttpResponse.json(todayPayload))
    );

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("Active Alerts")).toBeInTheDocument();
    });
    expect(screen.getByText("SGR below threshold")).toBeInTheDocument();
  });

  it("renders overdue task", async () => {
    server.use(
      http.get("*/agent/today", () => HttpResponse.json(todayPayload))
    );

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("Check aeration on Pond Alpha")).toBeInTheDocument();
    });
    expect(screen.getByText(/Overdue/i)).toBeInTheDocument();
  });

  it("calls dismiss mutation and shows toast on error", async () => {
    server.use(
      http.get("*/agent/today", () => HttpResponse.json(todayPayload)),
      http.delete("*/agent/alerts/:id", () => HttpResponse.json({ code: 500 }, { status: 500 }))
    );

    renderComponent();
    await screen.findByText("DO is critically low: 1.8 mg/L");

    const dismissButtons = screen.getAllByRole("button", { name: /Dismiss alert/ });
    await userEvent.click(dismissButtons[0]);

    await waitFor(() => {
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error" })
      );
    });
  });

  it("calls resolve mutation when resolve button clicked", async () => {
    let resolvedId = "";
    server.use(
      http.get("*/agent/today", () => HttpResponse.json(todayPayload)),
      http.patch("*/agent/alerts/:id/resolve", ({ params }) => {
        resolvedId = params.id as string;
        return HttpResponse.json({ code: 200, message: "OK", payload: {} });
      }),
      http.post("*/agent/control-loops", () => HttpResponse.json({ payload: { id: "loop-1" } })),
      http.get("*/agent/alerts", () => HttpResponse.json({ payload: { alerts: [] } }))
    );

    renderComponent();
    await screen.findByText("DO is critically low: 1.8 mg/L");

    const resolveButtons = screen.getAllByRole("button", { name: /Resolve alert/ });
    await userEvent.click(resolveButtons[0]);
    await userEvent.type(screen.getByLabelText("Action taken"), "Turn on backup aerator");
    await userEvent.click(screen.getByRole("button", { name: "Record action" }));

    await waitFor(() => {
      expect(resolvedId).toBe("alert-1");
    });
  });

  it("shows no-farm message when farm_id is not set", () => {
    useDashboardContextStore.getState().clearContext();
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayView />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText(/Select a farm/i)).toBeInTheDocument();
  });
});
