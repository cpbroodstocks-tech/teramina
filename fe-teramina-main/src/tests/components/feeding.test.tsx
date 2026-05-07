import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { server } from "../mocks/server";
import NewRationForm from "features/feeding/new-ration/index";

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

const mockSetToast = vi.fn();
vi.mock("store/toast.store", () => ({
  useToastStore: Object.assign(
    () => ({ setToast: mockSetToast }),
    { getState: () => ({ setToast: mockSetToast }) }
  ),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

// ── Helpers ────────────────────────────────────────────────────────────────

function renderForm({
  ration_id = "",
  ration_number = "1",
  onSubmit = vi.fn().mockResolvedValue(undefined),
  onClose = vi.fn(),
} = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <NewRationForm
        initialValue={{
          id: ration_id,
          value: [{ value: "" }, { value: "" }],
          ration_number,
        }}
        selectedFilter={{ cycle_id: "cycle-001", date: "2024-01-15" }}
        onSubmit={onSubmit}
        onClose={onClose}
      />
    </QueryClientProvider>
  );
  const [rationNumberInput, feedGivenInput, feedLeftoverInput] = screen.getAllByRole("textbox") as HTMLInputElement[];
  return {
    feedGivenInput,
    feedLeftoverInput,
    rationNumberInput,
    submitButton: screen.getByRole("button", { name: /SUBMIT/i }),
  };
}

// ── Suite ──────────────────────────────────────────────────────────────────

describe("NewRationForm (feeding record)", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders ration_number pre-filled and disabled", () => {
    const { rationNumberInput } = renderForm({ ration_number: "3" });
    expect(rationNumberInput.value).toBe("3");
    expect(rationNumberInput).toBeDisabled();
  });

  it("adds a new feeding record via POST when no ration_id", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();
    server.use(
      http.post("*/feeding/add-feeding", () => HttpResponse.json({ payload: {} }))
    );

    const { feedGivenInput, submitButton } = renderForm({ onSubmit, onClose });
    await user.type(feedGivenInput, "25");
    await user.click(submitButton);

    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    expect(onClose).toHaveBeenCalled();
    expect(mockSetToast).toHaveBeenCalledWith(
      expect.objectContaining({ variant: "success" })
    );
  });

  it("edits an existing record via PUT when ration_id is provided", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    server.use(
      http.put("*/feeding/edit-feeding", () => HttpResponse.json({ payload: {} }))
    );

    const { feedGivenInput, submitButton } = renderForm({ ration_id: "ration-abc", onSubmit });
    await user.type(feedGivenInput, "30");
    await user.click(submitButton);

    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    expect(mockSetToast).toHaveBeenCalledWith(
      expect.objectContaining({ variant: "success" })
    );
  });

  it("shows API error message in error toast", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("*/feeding/add-feeding", () =>
        HttpResponse.json({ message: "Duplicate entry for this date" }, { status: 400 })
      )
    );

    const { feedGivenInput, submitButton } = renderForm();
    await user.type(feedGivenInput, "20");
    await user.click(submitButton);

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error", text: "Duplicate entry for this date" })
      )
    );
  });

  it("falls back to generic error message when API provides none", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("*/feeding/add-feeding", () =>
        HttpResponse.json({}, { status: 500 })
      )
    );

    const { feedGivenInput, submitButton } = renderForm();
    await user.type(feedGivenInput, "20");
    await user.click(submitButton);

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error", text: "ADD_DATA_FAILED_MESSAGE" })
      )
    );
  });

  it("feed_given validation prevents submit when empty", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("*/feeding/add-feeding", () => HttpResponse.json({ payload: {} }))
    );

    const { submitButton } = renderForm();
    await user.click(submitButton);

    // If validation blocks the request, toast is never called
    await new Promise((r) => setTimeout(r, 100));
    expect(mockSetToast).not.toHaveBeenCalledWith(
      expect.objectContaining({ variant: "success" })
    );
  });
});
