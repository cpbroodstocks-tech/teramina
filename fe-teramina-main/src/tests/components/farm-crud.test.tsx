import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { server } from "../mocks/server";
import ModalFarmAdd from "features/farm/modal-add-farm";
import ModalFarmEdit from "features/farm/modal-edit-farm";
import ModalFarmDelete from "features/farm/modal-delete-farm";

// ── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

const mockSetToast = vi.fn();
vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: mockSetToast }),
}));

// Mock the complex NewFarm component with its cascading region selects
vi.mock("features/farm/new-farm", () => ({
  default: ({ formik }: { formik: any }) => (
    <form onSubmit={formik.handleSubmit}>
      <input
        aria-label="Farm Name"
        {...formik.register("name")}
      />
      <button
        type="button"
        data-testid="set-region"
        onClick={() => {
          formik.setValue("provinsi", JSON.stringify({ id: "11", name: "Aceh" }));
          formik.setValue("kabupaten", JSON.stringify({ id: "1101", name: "Simeulue" }));
          formik.setValue("kecamatan", JSON.stringify({ id: "1101010", name: "Teupah Selatan" }));
          formik.setValue("kelurahan", JSON.stringify({ id: "1101010001", name: "Latiung" }));
        }}
      >
        set-region
      </button>
      <button type="submit">SUBMIT</button>
    </form>
  ),
}));

// ── Helpers ────────────────────────────────────────────────────────────────

function renderComponent(component: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{component}</MemoryRouter>
    </QueryClientProvider>
  );
}

const farmListHandler = http.get("*/farm/list-farm", () =>
  HttpResponse.json({ payload: [] })
);

// ── ModalFarmAdd ───────────────────────────────────────────────────────────

describe("ModalFarmAdd", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
    server.use(farmListHandler);
  });

  it("opens dialog when ADD_FARM button is clicked", async () => {
    const user = userEvent.setup();
    renderComponent(<ModalFarmAdd />);

    expect(screen.queryByTestId("set-region")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "ADD_FARM" }));
    expect(await screen.findByTestId("set-region")).toBeInTheDocument();
  });

  it("sets region + types name + submits → POST called → success toast → dialog closes", async () => {
    const user = userEvent.setup();
    let capturedBody: Record<string, unknown> = {};

    server.use(
      http.post("*/farm/add-farm", async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ payload: { _id: "farm-1", name: "Test Farm" } });
      }),
      farmListHandler
    );

    renderComponent(<ModalFarmAdd />);
    await user.click(screen.getByRole("button", { name: "ADD_FARM" }));
    await screen.findByTestId("set-region");

    await user.click(screen.getByTestId("set-region"));
    await user.type(screen.getByLabelText("Farm Name"), "Test Farm");
    await user.click(screen.getByRole("button", { name: "SUBMIT" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "ADD_DATA_SUCCESS_MESSAGE" })
      )
    );

    expect(capturedBody.name).toBe("Test Farm");
    expect(capturedBody.location).toContain("Latiung");

    // Dialog should close after success
    await waitFor(() =>
      expect(screen.queryByTestId("set-region")).not.toBeInTheDocument()
    );
  });

  it("shows error toast when API returns 500", async () => {
    const user = userEvent.setup();

    server.use(
      http.post("*/farm/add-farm", () =>
        HttpResponse.json({ message: "Server error" }, { status: 500 })
      ),
      farmListHandler
    );

    renderComponent(<ModalFarmAdd />);
    await user.click(screen.getByRole("button", { name: "ADD_FARM" }));
    await screen.findByTestId("set-region");

    await user.click(screen.getByTestId("set-region"));
    await user.type(screen.getByLabelText("Farm Name"), "Test Farm");
    await user.click(screen.getByRole("button", { name: "SUBMIT" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error", text: "ADD_DATA_FAILED_MESSAGE" })
      )
    );
  });
});

// ── ModalFarmEdit ──────────────────────────────────────────────────────────

describe("ModalFarmEdit", () => {
  const farmData = { _id: "farm-1", name: "Old Farm" };

  beforeEach(() => {
    mockSetToast.mockClear();
    server.use(farmListHandler);
  });

  it("opens dialog, name field is pre-filled, sets region + submits → PUT called → success toast", async () => {
    const user = userEvent.setup();
    let putCalled = false;

    server.use(
      http.put("*/farm/update-farm", async () => {
        putCalled = true;
        return HttpResponse.json({});
      }),
      farmListHandler
    );

    renderComponent(<ModalFarmEdit data={farmData} />);

    // The edit button is the SVG pencil icon button (no text label)
    const buttons = screen.getAllByRole("button");
    const editBtn = buttons[0];
    await user.click(editBtn);

    // Wait for dialog to open
    await screen.findByTestId("set-region");

    // Name field should be pre-filled
    const nameInput = screen.getByLabelText("Farm Name");
    expect(nameInput).toHaveValue("Old Farm");

    await user.click(screen.getByTestId("set-region"));
    await user.click(screen.getByRole("button", { name: "SUBMIT" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "EDIT_DATA_SUCCESS_MESSAGE" })
      )
    );

    expect(putCalled).toBe(true);
  });
});

// ── ModalFarmDelete ────────────────────────────────────────────────────────

describe("ModalFarmDelete", () => {
  const farmData = { _id: "farm-1" };

  beforeEach(() => {
    mockSetToast.mockClear();
    server.use(farmListHandler);
  });

  it("clicking delete button opens ConfirmDelete dialog with YES and NO buttons", async () => {
    const user = userEvent.setup();
    renderComponent(<ModalFarmDelete data={farmData} />);

    expect(screen.queryByRole("button", { name: "YES" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button"));
    expect(await screen.findByRole("button", { name: "YES" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "NO" })).toBeInTheDocument();
  });

  it("click YES → DELETE called → success toast", async () => {
    const user = userEvent.setup();
    let deletedId = "";

    server.use(
      http.delete("*/farm/delete-farm", ({ request }) => {
        deletedId = new URL(request.url).searchParams.get("farm_id") ?? "";
        return HttpResponse.json({});
      }),
      farmListHandler
    );

    renderComponent(<ModalFarmDelete data={farmData} />);
    await user.click(screen.getByRole("button"));
    await user.click(await screen.findByRole("button", { name: "YES" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "DELETE_DATA_SUCCESS_MESSAGE" })
      )
    );

    expect(deletedId).toBe("farm-1");
  });

  it("shows error toast when DELETE API returns 500", async () => {
    const user = userEvent.setup();

    server.use(
      http.delete("*/farm/delete-farm", () =>
        HttpResponse.json({ message: "Server error" }, { status: 500 })
      ),
      farmListHandler
    );

    renderComponent(<ModalFarmDelete data={farmData} />);
    await user.click(screen.getByRole("button"));
    await user.click(await screen.findByRole("button", { name: "YES" }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error", text: "DELETE_DATA_FAILED_MESSAGE" })
      )
    );
  });

  it("click NO → dialog closes → no API call", async () => {
    const user = userEvent.setup();
    let deleteCalled = false;

    server.use(
      http.delete("*/farm/delete-farm", () => {
        deleteCalled = true;
        return HttpResponse.json({});
      })
    );

    renderComponent(<ModalFarmDelete data={farmData} />);
    await user.click(screen.getByRole("button"));
    await user.click(await screen.findByRole("button", { name: "NO" }));

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "YES" })).not.toBeInTheDocument()
    );

    expect(deleteCalled).toBe(false);
  });
});
