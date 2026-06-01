import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { server } from "../mocks/server";
import PondTimeline from "pages/dashboard/pond-timeline";

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => vi.fn() };
});

const timelinePayload = {
  payload: {
    cycle_id: "cycle-1",
    cycle_name: "Siklus A 2026",
    start_date: "2026-01-01T00:00:00",
    total_events: 3,
    events: [
      {
        type: "observation",
        doc: 10,
        description: "DO measured at 6.2 mg/L, temp 28°C",
        severity: null,
        tags: ["do", "temp"],
        date: null,
      },
      {
        type: "alert",
        doc: 15,
        description: "NH3 elevated: 0.05 mg/L",
        severity: "warning",
        tags: ["nh3"],
        date: null,
      },
      {
        type: "memory_advice",
        doc: null,
        description: "Added aeration for 2 hours, DO recovered",
        severity: null,
        tags: ["aeration"],
        date: "2026-01-16T08:00:00",
      },
    ],
  },
};

function renderComponent() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/dashboard/pond-timeline/cycle-1"]}>
        <Routes>
          <Route path="/dashboard/pond-timeline/:cycle_id" element={<PondTimeline />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("PondTimeline", () => {
  beforeEach(() => {
    server.use(
      http.get("*/agent/pond-timeline", () => HttpResponse.json(timelinePayload)),
      http.get("*/advisory/history", () => HttpResponse.json({ payload: { total_events: 0, events: [] } }))
    );
  });

  it("renders cycle name and total event count", async () => {
    renderComponent();

    expect(await screen.findByText(/Siklus A 2026/i)).toBeInTheDocument();
    expect(screen.getByText(/3 total events/i)).toBeInTheDocument();
  });

  it("renders all three events by default (All filter)", async () => {
    renderComponent();

    expect(await screen.findByText("DO measured at 6.2 mg/L, temp 28°C")).toBeInTheDocument();
    expect(screen.getByText("NH3 elevated: 0.05 mg/L")).toBeInTheDocument();
    expect(screen.getByText("Added aeration for 2 hours, DO recovered")).toBeInTheDocument();
  });

  it("filters to only observation events when Water is selected", async () => {
    renderComponent();

    await screen.findByText("DO measured at 6.2 mg/L, temp 28°C");

    const waterButton = screen.getByRole("button", { name: /^Water$/i });
    await userEvent.click(waterButton);

    expect(screen.getByText("DO measured at 6.2 mg/L, temp 28°C")).toBeInTheDocument();
    expect(screen.queryByText("NH3 elevated: 0.05 mg/L")).not.toBeInTheDocument();
    expect(screen.queryByText("Added aeration for 2 hours, DO recovered")).not.toBeInTheDocument();
  });

  it("filters to only alert events when Alerts is selected", async () => {
    renderComponent();

    await screen.findByText("NH3 elevated: 0.05 mg/L");

    const alertsButton = screen.getByRole("button", { name: /^Alerts$/i });
    await userEvent.click(alertsButton);

    expect(screen.queryByText("DO measured at 6.2 mg/L, temp 28°C")).not.toBeInTheDocument();
    expect(screen.getByText("NH3 elevated: 0.05 mg/L")).toBeInTheDocument();
  });

  it("filters to memory_advice events when Advice is selected", async () => {
    renderComponent();

    await screen.findByText("Added aeration for 2 hours, DO recovered");

    const adviceButton = screen.getByRole("button", { name: /^Advice$/i });
    await userEvent.click(adviceButton);

    expect(screen.queryByText("DO measured at 6.2 mg/L, temp 28°C")).not.toBeInTheDocument();
    expect(screen.getByText("Added aeration for 2 hours, DO recovered")).toBeInTheDocument();
  });

  it("renders linked advisory history for the cycle", async () => {
    server.use(
      http.get("*/advisory/history", () =>
        HttpResponse.json({
          payload: {
            total_events: 1,
            events: [
              {
                id: "case-1",
                type: "advisory_case",
                case_id: "case-1",
                case_type: "farm_diagnostic",
                status: "in_review",
                title: "DOC 45 mortality review",
                description: "Farm Diagnostic: DOC 45 mortality review",
                created_at: "2026-01-20T08:00:00",
                url: "/dashboard/advisory/case-1",
              },
            ],
          },
        })
      )
    );
    renderComponent();

    expect(await screen.findByText("Farm Diagnostic: DOC 45 mortality review")).toBeInTheDocument();
    expect(screen.getByText(/4 total events/i)).toBeInTheDocument();

    const advisoryButton = screen.getByRole("button", { name: /^Advisory$/i });
    await userEvent.click(advisoryButton);

    expect(screen.queryByText("NH3 elevated: 0.05 mg/L")).not.toBeInTheDocument();
    expect(screen.getByText("Farm Diagnostic: DOC 45 mortality review")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Open advisory case/i })).toBeInTheDocument();
  });

  it("shows empty state when filter matches no events", async () => {
    server.use(
      http.get("*/agent/pond-timeline", () =>
        HttpResponse.json({
          payload: {
            cycle_id: "cycle-1",
            cycle_name: "Empty Cycle",
            start_date: null,
            total_events: 1,
            events: [{ type: "observation", doc: 5, description: "Water ok", severity: null, tags: [], date: null }],
          },
        })
      )
    );
    renderComponent();

    await screen.findByText("Water ok");

    const alertsButton = screen.getByRole("button", { name: /^Alerts$/i });
    await userEvent.click(alertsButton);

    expect(screen.getByText(/No events found/i)).toBeInTheDocument();
  });

  it("shows error state when request fails", async () => {
    server.use(
      http.get("*/agent/pond-timeline", () => HttpResponse.json({ error: "Not found" }, { status: 404 }))
    );
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/Failed to load pond timeline/i)).toBeInTheDocument();
    });
  });
});
