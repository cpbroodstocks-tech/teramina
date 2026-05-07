import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach } from "vitest";
import dayjs from "dayjs";
import { server } from "../mocks/server";
import ModalCycleAdd from "features/cycle/modal-add-cycle";
import ModalCycleDelete from "features/cycle/modal-delete-cycle";

// ── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

const mockSetToast = vi.fn();
vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: mockSetToast }),
}));

// Mock StaticDatePicker to avoid complex calendar rendering
vi.mock("@mui/x-date-pickers/StaticDatePicker", () => ({
  StaticDatePicker: ({ onChange }: { onChange: (v: any) => void }) => (
    <button
      type="button"
      data-testid="pick-date"
      onClick={() => onChange(dayjs("2024-03-01"))}
    >
      Pick Date
    </button>
  ),
}));

// Mock LocalizationProvider to just render children
vi.mock("@mui/x-date-pickers/LocalizationProvider", () => ({
  LocalizationProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// ── Helpers ────────────────────────────────────────────────────────────────

const POND_ID = "pond-1";

function renderComponent(
  component: React.ReactElement,
  path = `/pond/${POND_ID}/cycles`,
  routePath = "/pond/:pond_id/cycles"
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path={routePath} element={component} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const cycleListHandler = http.get("*/cycle/list-cycles", () =>
  HttpResponse.json({ payload: [] })
);

// ── ModalCycleAdd ──────────────────────────────────────────────────────────

describe("ModalCycleAdd", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
    server.use(cycleListHandler);
  });

  it("opens dialog when ADD_CYCLE button is clicked", async () => {
    const user = userEvent.setup();
    renderComponent(<ModalCycleAdd />);

    expect(screen.queryByTestId("pick-date")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "ADD_CYCLE" }));
    expect(await screen.findByTestId("pick-date")).toBeInTheDocument();
  });

  it("types name + picks date → submits → POST with correct body → success toast", async () => {
    const user = userEvent.setup();
    let capturedBody: Record<string, unknown> = {};
    let capturedUrl = "";

    server.use(
      http.post("*/cycle/add-cycle", async ({ request }) => {
        capturedUrl = request.url;
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ payload: { _id: "cycle-1" } });
      }),
      cycleListHandler
    );

    renderComponent(<ModalCycleAdd />);
    await user.click(screen.getByRole("button", { name: "ADD_CYCLE" }));
    await screen.findByTestId("pick-date");

    // Type the cycle name into the name text field
    const nameInput = screen.getByRole("textbox");
    await user.type(nameInput, "Spring Cycle");

    // Click the mocked date picker
    await user.click(screen.getByTestId("pick-date"));

    await user.click(screen.getByRole("button", { name: "SUBMIT" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "ADD_DATA_SUCCESS_MESSAGE" })
      )
    );

    expect(capturedBody.name).toBe("Spring Cycle");
    expect(capturedBody.start_date).toBe("03/01/2024");
    expect(capturedUrl).toContain(`pond_id=${POND_ID}`);
  });

  it("shows error toast when API returns 500", async () => {
    const user = userEvent.setup();

    server.use(
      http.post("*/cycle/add-cycle", () =>
        HttpResponse.json({ message: "Server error" }, { status: 500 })
      ),
      cycleListHandler
    );

    renderComponent(<ModalCycleAdd />);
    await user.click(screen.getByRole("button", { name: "ADD_CYCLE" }));
    await screen.findByTestId("pick-date");

    const nameInput = screen.getByRole("textbox");
    await user.type(nameInput, "Spring Cycle");
    await user.click(screen.getByTestId("pick-date"));
    await user.click(screen.getByRole("button", { name: "SUBMIT" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error", text: "ADD_DATA_FAILED_MESSAGE" })
      )
    );
  });
});

// ── ModalCycleDelete ───────────────────────────────────────────────────────

describe("ModalCycleDelete", () => {
  const cycleData = { _id: "cycle-1" };

  beforeEach(() => {
    mockSetToast.mockClear();
    server.use(cycleListHandler);
  });

  it("click YES → DELETE called → success toast", async () => {
    const user = userEvent.setup();
    let deletedId = "";

    server.use(
      http.delete("*/cycle/delete-cycle", ({ request }) => {
        deletedId = new URL(request.url).searchParams.get("cycle_id") ?? "";
        return HttpResponse.json({});
      }),
      cycleListHandler
    );

    renderComponent(<ModalCycleDelete data={cycleData} />);
    await user.click(screen.getByRole("button"));
    await user.click(await screen.findByRole("button", { name: "YES" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "DELETE_DATA_SUCCESS_MESSAGE" })
      )
    );

    expect(deletedId).toBe("cycle-1");
  });

  it("click NO → dialog closes → no API call", async () => {
    const user = userEvent.setup();
    let deleteCalled = false;

    server.use(
      http.delete("*/cycle/delete-cycle", () => {
        deleteCalled = true;
        return HttpResponse.json({});
      })
    );

    renderComponent(<ModalCycleDelete data={cycleData} />);
    await user.click(screen.getByRole("button"));
    await user.click(await screen.findByRole("button", { name: "NO" }));

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "YES" })).not.toBeInTheDocument()
    );

    expect(deleteCalled).toBe(false);
  });
});
