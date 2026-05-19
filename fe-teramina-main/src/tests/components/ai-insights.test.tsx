import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { server } from "../mocks/server";
import AiInsights from "features/cycle-detail/ai-insights/index";

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

const mockSetToast = vi.fn();
vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: mockSetToast }),
}));

const CYCLE_ID = "cycle-ai-001";

function renderComponent() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/cycle/${CYCLE_ID}`]}>
        <Routes>
          <Route path="/cycle/:cycle_id" element={<AiInsights />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const sampleInsight = {
  summary: "Farm is performing well overall",
  performance_score: 82,
  metrics: [
    { name: "Survival Rate", current_value: 88, unit: "%", status: "good" },
    { name: "FCR", current_value: 1.4, unit: null, status: "warning" },
  ],
  anomalies: [
    { severity: "low", description: "Slight DO drop on day 30", recommendation: "Increase aeration" },
  ],
  recommendations: [
    { priority: "medium", action: "Adjust feeding schedule", reason: "Based on FCR trend" },
  ],
  forecast_outlook: "Harvest expected in 15 days",
};

function insightPayload(overrides = {}) {
  return { payload: { insight: { ...sampleInsight, ...overrides } } };
}

function streamInsightResponse(insight) {
  const insightJson = JSON.stringify(insight);
  const body =
    `data: {"type":"chunk","text":${JSON.stringify(insightJson)}}\n` +
    "data: {\"type\":\"done\"}\n\n";

  return new Response(body, { headers: { "Content-Type": "text/event-stream" } });
}

describe("AiInsights", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ── Type selector ─────────────────────────────────────────────────────────

  it("renders all 6 insight type buttons", () => {
    renderComponent();
    for (const label of ["performance", "water quality", "feeding", "harvest", "economics", "weekly"]) {
      expect(screen.getByRole("button", { name: new RegExp(label, "i") })).toBeInTheDocument();
    }
  });

  it("performance type button is selected (contained) by default", () => {
    renderComponent();
    const btn = screen.getByRole("button", { name: /^performance$/i });
    expect(btn).toHaveClass("MuiButton-contained");
  });

  it("clicking a type button changes the active selection", async () => {
    const user = userEvent.setup();
    renderComponent();

    await user.click(screen.getByRole("button", { name: /^feeding$/i }));

    expect(screen.getByRole("button", { name: /^feeding$/i })).toHaveClass("MuiButton-contained");
    expect(screen.getByRole("button", { name: /^performance$/i })).not.toHaveClass("MuiButton-contained");
  });

  // ── Generate (non-streaming) ──────────────────────────────────────────────

  it("Generate button fetches and renders summary + score", async () => {
    const user = userEvent.setup();
    server.use(
      http.get("*/summarize/insight/stream", () => streamInsightResponse(sampleInsight))
    );

    renderComponent();
    await user.click(screen.getByRole("button", { name: /^Generate$/i }));

    expect(await screen.findByText("Farm is performing well overall")).toBeInTheDocument();
    expect(screen.getByText("82/100")).toBeInTheDocument();
  });

  it("renders metrics, anomalies, and recommendations after generate", async () => {
    const user = userEvent.setup();
    server.use(
      http.get("*/summarize/insight/stream", () => streamInsightResponse(sampleInsight))
    );

    renderComponent();
    await user.click(screen.getByRole("button", { name: /^Generate$/i }));

    expect(await screen.findByText("Survival Rate")).toBeInTheDocument();
    expect(screen.getByText("Slight DO drop on day 30")).toBeInTheDocument();
    expect(screen.getByText("Adjust feeding schedule")).toBeInTheDocument();
    expect(screen.getByText("Harvest expected in 15 days")).toBeInTheDocument();
  });

  it("shows error toast when Generate API fails", async () => {
    const user = userEvent.setup();
    server.use(
      http.get("*/summarize/insight/stream", () =>
        HttpResponse.error()
      )
    );

    renderComponent();
    await user.click(screen.getByRole("button", { name: /^Generate$/i }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error", text: "Streaming failed" })
      )
    );
  });

  // ── Load cached ───────────────────────────────────────────────────────────

  it("Load Cached button shows Cached chip and renders insight", async () => {
    const user = userEvent.setup();
    server.use(
      http.get("*/summarize/insight/cached", () => HttpResponse.json(insightPayload()))
    );

    renderComponent();
    await user.click(screen.getByRole("button", { name: /Load Cached/i }));

    expect(await screen.findByText("Farm is performing well overall")).toBeInTheDocument();
    expect(screen.getByText("Cached")).toBeInTheDocument();
  });

  it("shows error toast when Load Cached API fails", async () => {
    const user = userEvent.setup();
    server.use(
      http.get("*/summarize/insight/cached", () =>
        HttpResponse.json({ message: "not found" }, { status: 404 })
      )
    );

    renderComponent();
    await user.click(screen.getByRole("button", { name: /Load Cached/i }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error", text: "Failed to load insight" })
      )
    );
  });

  // ── Streaming ─────────────────────────────────────────────────────────────

  it("Generate (Live) renders summary from streaming chunks", async () => {
    const user = userEvent.setup();
    const insightJson = JSON.stringify({
      summary: "Streamed insight summary",
      performance_score: 75,
    });

    server.use(
      http.get("*/summarize/insight/stream", () =>
        streamInsightResponse(JSON.parse(insightJson))
      )
    );

    renderComponent();
    await user.click(screen.getByRole("button", { name: /^Generate$/i }));

    expect(await screen.findByText("Streamed insight summary")).toBeInTheDocument();
  });

  it("shows error toast when streaming returns an error event", async () => {
    const user = userEvent.setup();
    const body = "data: {\"type\":\"error\",\"message\":\"Stream unavailable\"}\n\n";

    server.use(
      http.get("*/summarize/insight/stream", () =>
        new Response(body, { headers: { "Content-Type": "text/event-stream" } })
      )
    );

    renderComponent();
    await user.click(screen.getByRole("button", { name: /^Generate$/i }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error", text: "Stream unavailable" })
      )
    );
  });
});
