import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { server } from "../mocks/server";
import BenchmarkSection from "features/cycle-detail/benchmark/index";

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

const mockSetToast = vi.fn();
vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: mockSetToast }),
}));

const CYCLE_ID = "cycle-bench-001";

function renderComponent() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/cycle/${CYCLE_ID}`]}>
        <Routes>
          <Route path="/cycle/:cycle_id" element={<BenchmarkSection />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const notOptedIn = { payload: { opted_in: false } };

function optedInPayload(metrics: Record<string, unknown> = {}) {
  return { payload: { opted_in: true, performance: { metrics } } };
}

describe("BenchmarkSection", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ── Opt-in UI ─────────────────────────────────────────────────────────────

  describe("opt-in UI", () => {
    beforeEach(() => {
      server.use(
        http.get("*/benchmark/my-performance", () => HttpResponse.json(notOptedIn))
      );
    });

    it("renders opt-in form when not opted in", async () => {
      renderComponent();
      expect(await screen.findByText("Farm Performance Benchmarking")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Enable Benchmarking/i })).toBeInTheDocument();
    });

    it("Enable Benchmarking button is disabled when checkbox is unchecked", async () => {
      renderComponent();
      await screen.findByText("Farm Performance Benchmarking");
      expect(screen.getByRole("button", { name: /Enable Benchmarking/i })).toBeDisabled();
    });

    it("Enable Benchmarking button enables after checkbox is checked", async () => {
      const user = userEvent.setup();
      renderComponent();
      await screen.findByText("Farm Performance Benchmarking");
      await user.click(screen.getByRole("checkbox"));
      expect(screen.getByRole("button", { name: /Enable Benchmarking/i })).toBeEnabled();
    });

    it("opts in, transitions away from opt-in UI", async () => {
      const user = userEvent.setup();
      let statusCall = 0;
      server.use(
        http.get("*/benchmark/my-performance", () => {
          statusCall++;
          return HttpResponse.json(statusCall === 1 ? notOptedIn : optedInPayload());
        }),
        http.post("*/benchmark/opt-in", () => HttpResponse.json({ payload: {} }))
      );

      renderComponent();
      await screen.findByText("Farm Performance Benchmarking");
      await user.click(screen.getByRole("checkbox"));
      await user.click(screen.getByRole("button", { name: /Enable Benchmarking/i }));

      await waitFor(() =>
        expect(screen.queryByText("Farm Performance Benchmarking")).not.toBeInTheDocument()
      );
    });

    it("shows error toast when opt-in API fails", async () => {
      const user = userEvent.setup();
      server.use(
        http.post("*/benchmark/opt-in", () =>
          HttpResponse.json({ message: "server error" }, { status: 500 })
        )
      );

      renderComponent();
      await screen.findByText("Farm Performance Benchmarking");
      await user.click(screen.getByRole("checkbox"));
      await user.click(screen.getByRole("button", { name: /Enable Benchmarking/i }));

      await waitFor(() =>
        expect(mockSetToast).toHaveBeenCalledWith(
          expect.objectContaining({ variant: "error", text: "Failed to opt in" })
        )
      );
    });
  });

  // ── Metrics view ──────────────────────────────────────────────────────────

  describe("metrics view when opted in", () => {
    it("renders metric cards with above/below average chips", async () => {
      const metrics = {
        survival_rate: { my_value: 85, p25: 70, p50: 80, p75: 90, cohort_size: 10 },
        fcr: { my_value: 1.2, p25: 1.0, p50: 1.5, p75: 2.0, cohort_size: 10 },
      };
      server.use(
        http.get("*/benchmark/my-performance", () =>
          HttpResponse.json(optedInPayload(metrics))
        )
      );

      renderComponent();

      expect(await screen.findByText("survival rate")).toBeInTheDocument();
      expect(screen.getByText("Above Average")).toBeInTheDocument();
      expect(screen.getByText("Below Average")).toBeInTheDocument();
    });

    it("shows insufficient data message when cohort_size < 5", async () => {
      const metrics = {
        survival_rate: { my_value: 85, p25: 70, p50: 80, p75: 90, cohort_size: 3 },
      };
      server.use(
        http.get("*/benchmark/my-performance", () =>
          HttpResponse.json(optedInPayload(metrics))
        )
      );

      renderComponent();
      expect(await screen.findByText("Insufficient data (need 5+ farms)")).toBeInTheDocument();
    });

    it("shows p25/p50/p75 labels when cohort_size >= 5", async () => {
      const metrics = {
        survival_rate: { my_value: 85, p25: 70, p50: 80, p75: 90, cohort_size: 8 },
      };
      server.use(
        http.get("*/benchmark/my-performance", () =>
          HttpResponse.json(optedInPayload(metrics))
        )
      );

      renderComponent();
      expect(await screen.findByText(/p50: 80/)).toBeInTheDocument();
    });

    it("opts out and returns to opt-in UI", async () => {
      const user = userEvent.setup();
      let statusCall = 0;
      server.use(
        http.get("*/benchmark/my-performance", () => {
          statusCall++;
          return HttpResponse.json(statusCall === 1 ? optedInPayload() : notOptedIn);
        }),
        http.post("*/benchmark/opt-out", () => HttpResponse.json({ payload: {} }))
      );

      renderComponent();
      const optOutBtn = await screen.findByRole("button", { name: /Opt Out/i });
      await user.click(optOutBtn);

      await waitFor(() =>
        expect(screen.getByText("Farm Performance Benchmarking")).toBeInTheDocument()
      );
    });

    it("shows error toast when opt-out API fails", async () => {
      const user = userEvent.setup();
      server.use(
        http.get("*/benchmark/my-performance", () => HttpResponse.json(optedInPayload())),
        http.post("*/benchmark/opt-out", () =>
          HttpResponse.json({ message: "error" }, { status: 500 })
        )
      );

      renderComponent();
      const optOutBtn = await screen.findByRole("button", { name: /Opt Out/i });
      await user.click(optOutBtn);

      await waitFor(() =>
        expect(mockSetToast).toHaveBeenCalledWith(
          expect.objectContaining({ variant: "error", text: "Failed to opt out" })
        )
      );
    });
  });
});
