import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { server } from "../mocks/server";
import FeedingRecommendation from "features/cycle-detail/feeding-recommendation/index";

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

const mockSetToast = vi.fn();
vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: mockSetToast }),
}));

const CYCLE_ID = "cycle-feed-rec-001";

function renderComponent() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/cycle/${CYCLE_ID}`]}>
        <Routes>
          <Route path="/cycle/:cycle_id" element={<FeedingRecommendation />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const baseRecommendation = {
  payload: {
    recommended_ration_kg: 12.5,
    doc: 45,
    adjustment_reason: "Based on current biomass and FCR trend",
    model_layer: "biomass_model",
  },
};

describe("FeedingRecommendation", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
    server.use(
      http.get("*/feeding/recommendation", () => HttpResponse.json(baseRecommendation)),
      http.post("*/agent/control-loops", () => HttpResponse.json({ payload: { id: "loop-1" } }))
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("displays the recommended ration kg", async () => {
    renderComponent();
    expect(await screen.findByText("12.5")).toBeInTheDocument();
  });

  it("displays adjustment reason", async () => {
    renderComponent();
    expect(await screen.findByText("Based on current biomass and FCR trend")).toBeInTheDocument();
  });

  it("displays model layer", async () => {
    renderComponent();
    expect(await screen.findByText(/biomass_model/)).toBeInTheDocument();
  });

  it("Accept button fires success toast", async () => {
    const user = userEvent.setup();
    renderComponent();
    await screen.findByText("12.5");
    await user.click(screen.getByRole("button", { name: /Accept/i }));
    expect(mockSetToast).toHaveBeenCalledWith(
      expect.objectContaining({ variant: "success", text: "Recommendation accepted and follow-up scheduled" })
    );
  });

  it("Override button toggles override form visibility", async () => {
    const user = userEvent.setup();
    renderComponent();
    await screen.findByText("12.5");

    expect(screen.queryByLabelText(/Actual kg/i)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /^Override$/i }));
    expect(screen.getByLabelText(/Actual kg/i)).toBeInTheDocument();
  });

  it("Cancel hides the override form", async () => {
    const user = userEvent.setup();
    renderComponent();
    await screen.findByText("12.5");
    await user.click(screen.getByRole("button", { name: /^Override$/i }));
    await user.click(screen.getByRole("button", { name: /Cancel/i }));
    expect(screen.queryByLabelText(/Actual kg/i)).not.toBeInTheDocument();
  });

  it("Submit is disabled when actual kg is empty", async () => {
    const user = userEvent.setup();
    renderComponent();
    await screen.findByText("12.5");
    await user.click(screen.getByRole("button", { name: /^Override$/i }));
    expect(screen.getByRole("button", { name: /Submit/i })).toBeDisabled();
  });

  it("submits override successfully and shows 'Override recorded'", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("*/feeding/recommendation/override", () => HttpResponse.json({ payload: {} }))
    );

    renderComponent();
    await screen.findByText("12.5");
    await user.click(screen.getByRole("button", { name: /^Override$/i }));
    await user.type(screen.getByLabelText(/Actual kg/i), "10");
    await user.type(screen.getByLabelText(/Reason/i), "Pond conditions");
    await user.click(screen.getByRole("button", { name: /Submit/i }));

    expect(await screen.findByText("Override recorded")).toBeInTheDocument();
    expect(mockSetToast).toHaveBeenCalledWith(
      expect.objectContaining({ variant: "success", text: "Override recorded and follow-up scheduled" })
    );
  });

  it("shows error toast when override API fails", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("*/feeding/recommendation/override", () =>
        HttpResponse.json({ message: "quota exceeded" }, { status: 429 })
      )
    );

    renderComponent();
    await screen.findByText("12.5");
    await user.click(screen.getByRole("button", { name: /^Override$/i }));
    await user.type(screen.getByLabelText(/Actual kg/i), "10");
    await user.click(screen.getByRole("button", { name: /Submit/i }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error", text: "Failed to record override" })
      )
    );
  });
});
