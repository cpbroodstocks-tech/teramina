import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { server } from "../mocks/server";
import ModalAddHarvestRecord from "widgets/harvest/components/modal-add-harvest-record";

// ── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

const mockSetToast = vi.fn();
vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: mockSetToast }),
}));

// ── Helpers ────────────────────────────────────────────────────────────────

const mockRefetch = vi.fn();

const defaultProps = {
  selectedFilter: { cycle_id: "cycle-1" },
  currentData: { rows: [] },
  refetch: mockRefetch,
};

function renderComponent(props = defaultProps) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ModalAddHarvestRecord {...props} />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

// ── ModalAddHarvestRecord ──────────────────────────────────────────────────

describe("ModalAddHarvestRecord", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
    mockRefetch.mockClear();
  });

  it("opens dialog when ADD_HARVEST_RECORD button is clicked", async () => {
    const user = userEvent.setup();
    renderComponent();

    expect(screen.queryByText("DOC")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "ADD_HARVEST_RECORD" }));
    expect(await screen.findByText("DOC")).toBeInTheDocument();
  });

  it("selects partial harvest, fills fields, submits → POST called → success toast → refetch called", async () => {
    const user = userEvent.setup();
    let postCalled = false;
    let capturedUrl = "";

    server.use(
      http.post("*/harvest/add-harvest-record", async ({ request }) => {
        postCalled = true;
        capturedUrl = request.url;
        return HttpResponse.json({ payload: {} });
      })
    );

    renderComponent();
    await user.click(screen.getByRole("button", { name: "ADD_HARVEST_RECORD" }));
    await screen.findByText("DOC");

    // Select "partial" harvest type radio
    const partialRadio = screen.getByRole("radio", { name: "Partial" });
    await user.click(partialRadio);

    // Fill in the text fields. They are registered with react-hook-form via register()
    // and rendered as <TextField /> components — they render as textbox roles.
    const textboxes = screen.getAllByRole("textbox");
    // harvest_doc, harvest_biomass, harvest_revenue
    await user.type(textboxes[0], "60");
    await user.type(textboxes[1], "500");
    await user.type(textboxes[2], "2000000");

    await user.click(screen.getByRole("button", { name: "SUBMIT" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "ADD_DATA_SUCCESS_MESSAGE" })
      )
    );

    expect(postCalled).toBe(true);
    expect(capturedUrl).toContain("cycle_id=cycle-1");
    expect(mockRefetch).toHaveBeenCalled();
  });

  it("shows error toast when API fails", async () => {
    const user = userEvent.setup();

    server.use(
      http.post("*/harvest/add-harvest-record", () =>
        HttpResponse.json({ message: "Server error" }, { status: 500 })
      )
    );

    renderComponent();
    await user.click(screen.getByRole("button", { name: "ADD_HARVEST_RECORD" }));
    await screen.findByText("DOC");

    const partialRadio = screen.getByRole("radio", { name: "Partial" });
    await user.click(partialRadio);

    const textboxes = screen.getAllByRole("textbox");
    await user.type(textboxes[0], "60");
    await user.type(textboxes[1], "500");
    await user.type(textboxes[2], "2000000");

    await user.click(screen.getByRole("button", { name: "SUBMIT" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error" })
      )
    );
  });
});
