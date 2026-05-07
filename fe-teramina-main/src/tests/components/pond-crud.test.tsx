import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { server } from "../mocks/server";
import ModalPondAdd from "features/pond/modal-add-pond";
import ModalPondDelete from "features/pond/modal-delete-pond";

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

const FARM_ID = "farm-1";
const POND_ID = "pond-1";

function renderComponent(
  component: React.ReactElement,
  path = `/farm/${FARM_ID}/ponds`,
  routePath = "/farm/:farm_id/ponds"
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

const pondListHandler = http.get("*/pond/list-pond", () =>
  HttpResponse.json({ payload: [] })
);

// ── ModalPondAdd ───────────────────────────────────────────────────────────

describe("ModalPondAdd", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
    server.use(pondListHandler);
  });

  it("opens dialog when ADD_POND button is clicked", async () => {
    const user = userEvent.setup();
    renderComponent(<ModalPondAdd />);

    // form is not visible until dialog opens
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "ADD_POND" }));

    // The name text field should appear inside the dialog
    expect(await screen.findByRole("button", { name: "SUBMIT" })).toBeInTheDocument();
  });

  it("fills name + size + submits → POST called with correct body → success toast", async () => {
    const user = userEvent.setup();
    let capturedBody: Record<string, unknown> = {};
    let capturedUrl = "";

    server.use(
      http.post("*/pond/add-pond", async ({ request }) => {
        capturedUrl = request.url;
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ payload: { _id: "pond-1" } });
      }),
      pondListHandler
    );

    renderComponent(<ModalPondAdd />);
    await user.click(screen.getByRole("button", { name: "ADD_POND" }));
    await screen.findByRole("button", { name: "SUBMIT" });

    // The form renders two text inputs: name (text) and size (number)
    const inputs = screen.getAllByRole("textbox");
    // name field
    const nameInput = inputs[0];
    await user.type(nameInput, "Test Pond");

    // size field is type="number", use spinbutton role
    const sizeInput = screen.getByRole("spinbutton");
    await user.type(sizeInput, "500");

    await user.click(screen.getByRole("button", { name: "SUBMIT" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "ADD_DATA_SUCCESS_MESSAGE" })
      )
    );

    expect(capturedBody.name).toBe("Test Pond");
    expect(capturedBody.size).toBe(500);
    // defaultValues for construction and shape are already set to hdpe/persegi
    expect(capturedBody.pond_construction).toBe("HDPE");
    expect(capturedBody.pond_shape).toBe("Persegi");
    expect(capturedUrl).toContain(`farm_id=${FARM_ID}`);
  });

  it("shows error toast when API returns 500", async () => {
    const user = userEvent.setup();

    server.use(
      http.post("*/pond/add-pond", () =>
        HttpResponse.json({ message: "Server error" }, { status: 500 })
      ),
      pondListHandler
    );

    renderComponent(<ModalPondAdd />);
    await user.click(screen.getByRole("button", { name: "ADD_POND" }));
    await screen.findByRole("button", { name: "SUBMIT" });

    const inputs = screen.getAllByRole("textbox");
    await user.type(inputs[0], "Test Pond");
    const sizeInput = screen.getByRole("spinbutton");
    await user.type(sizeInput, "500");

    await user.click(screen.getByRole("button", { name: "SUBMIT" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error", text: "ADD_DATA_FAILED_MESSAGE" })
      )
    );
  });
});

// ── ModalPondDelete ────────────────────────────────────────────────────────

describe("ModalPondDelete", () => {
  const pondData = { _id: POND_ID };

  beforeEach(() => {
    mockSetToast.mockClear();
    server.use(pondListHandler);
  });

  it("click delete → confirm dialog → YES → DELETE called → success toast", async () => {
    const user = userEvent.setup();
    let deletedId = "";

    server.use(
      http.delete("*/pond/delete-pond", ({ request }) => {
        deletedId = new URL(request.url).searchParams.get("pond_id") ?? "";
        return HttpResponse.json({});
      }),
      pondListHandler
    );

    renderComponent(<ModalPondDelete data={pondData} />);

    // The delete button (SVG trash icon)
    await user.click(screen.getByRole("button"));
    await user.click(await screen.findByRole("button", { name: "YES" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "DELETE_DATA_SUCCESS_MESSAGE" })
      )
    );

    expect(deletedId).toBe(POND_ID);
  });

  it("click NO → dialog closes → no API call", async () => {
    const user = userEvent.setup();
    let deleteCalled = false;

    server.use(
      http.delete("*/pond/delete-pond", () => {
        deleteCalled = true;
        return HttpResponse.json({});
      })
    );

    renderComponent(<ModalPondDelete data={pondData} />);
    await user.click(screen.getByRole("button"));
    await user.click(await screen.findByRole("button", { name: "NO" }));

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "YES" })).not.toBeInTheDocument()
    );

    expect(deleteCalled).toBe(false);
  });
});
