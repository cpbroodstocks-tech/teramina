import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { server } from "../mocks/server";
import ModalPopulateAdd from "features/cycle-detail/modal-add-populate/index";
import ButtonDownloadData from "features/cycle-detail/download-data/index";

// ── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

const mockSetToast = vi.fn();
vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: mockSetToast }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("components/dropzone", () => ({
  default: ({ changeFile }: { changeFile: (files: File[]) => void }) => (
    <input
      type="file"
      data-testid="dropzone-input"
      onChange={(e) => changeFile(Array.from(e.target.files ?? []))}
    />
  ),
}));

// ── Helpers ────────────────────────────────────────────────────────────────

const CYCLE_ID = "cycle-pop-001";

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function renderModal() {
  return render(
    <QueryClientProvider client={makeQueryClient()}>
      <MemoryRouter initialEntries={[`/cycle/${CYCLE_ID}`]}>
        <Routes>
          <Route path="/cycle/:cycle_id" element={<ModalPopulateAdd data={{}} />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

function renderDownloadButton() {
  return render(
    <QueryClientProvider client={makeQueryClient()}>
      <MemoryRouter initialEntries={[`/cycle/${CYCLE_ID}`]}>
        <Routes>
          <Route path="/cycle/:cycle_id" element={<ButtonDownloadData />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

// ── Suite ──────────────────────────────────────────────────────────────────

describe("ModalPopulateAdd", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the open button", () => {
    renderModal();
    expect(screen.getByRole("button", { name: /ADD_CYCLE_POPULATION/i })).toBeInTheDocument();
  });

  it("opens dialog when button is clicked", async () => {
    const user = userEvent.setup();
    renderModal();
    await user.click(screen.getByRole("button", { name: /ADD_CYCLE_POPULATION/i }));
    expect(await screen.findByText("UPLOAD_CYCLE_DATA")).toBeInTheDocument();
  });

  it("submit button is enabled after file is selected", async () => {
    const user = userEvent.setup();
    renderModal();
    await user.click(screen.getByRole("button", { name: /ADD_CYCLE_POPULATION/i }));
    await screen.findByText("UPLOAD_CYCLE_DATA");

    const file = new File(["col1,col2\n1,2"], "data.csv", { type: "text/csv" });
    const input = screen.getByTestId("dropzone-input");
    await user.upload(input, file);

    expect(screen.getByRole("button", { name: /UPLOAD_FILE/i })).not.toBeDisabled();
  });

  it("successful upload closes dialog and shows success toast", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("*/cycle-data/populate-cycle-data", () => HttpResponse.json({ payload: {} }))
    );

    renderModal();
    await user.click(screen.getByRole("button", { name: /ADD_CYCLE_POPULATION/i }));
    await screen.findByText("UPLOAD_CYCLE_DATA");

    const file = new File(["col1,col2\n1,2"], "data.csv", { type: "text/csv" });
    await user.upload(screen.getByTestId("dropzone-input"), file);
    await user.click(screen.getByRole("button", { name: /UPLOAD_FILE/i }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success" })
      )
    );
  });

  it("upload failure shows error toast", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("*/cycle-data/populate-cycle-data", () =>
        HttpResponse.json({ message: "Invalid file format" }, { status: 400 })
      )
    );

    renderModal();
    await user.click(screen.getByRole("button", { name: /ADD_CYCLE_POPULATION/i }));
    await screen.findByText("UPLOAD_CYCLE_DATA");

    const file = new File(["col1,col2\n1,2"], "data.csv", { type: "text/csv" });
    await user.upload(screen.getByTestId("dropzone-input"), file);
    await user.click(screen.getByRole("button", { name: /UPLOAD_FILE/i }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error", text: "Invalid file format" })
      )
    );
  });

  it("download dummy data button triggers GET and downloads file", async () => {
    const user = userEvent.setup();
    const blob = new Blob(["dummy data"], { type: "text/csv" });
    server.use(
      http.get("*/dashboard/download-dummy", () => HttpResponse.arrayBuffer(new ArrayBuffer(8)))
    );

    const mockCreateObjectURL = vi.fn().mockReturnValue("blob:http://localhost/dummy");
    const mockRevokeObjectURL = vi.fn();
    const mockAppendChild = vi.spyOn(document.body, "appendChild").mockImplementation((el) => el);
    const mockRemoveChild = vi.spyOn(document.body, "removeChild").mockImplementation((el) => el);
    vi.stubGlobal("URL", { ...URL, createObjectURL: mockCreateObjectURL, revokeObjectURL: mockRevokeObjectURL });

    localStorage.setItem("selectedCycleStartDate", "2024-01-01");

    renderModal();
    await user.click(screen.getByRole("button", { name: /ADD_CYCLE_POPULATION/i }));
    await screen.findByText("UPLOAD_CYCLE_DATA");
    await user.click(screen.getByText("DOWNLOAD_EXAMPLE_DATA"));

    await waitFor(() => expect(mockCreateObjectURL).toHaveBeenCalled());

    mockAppendChild.mockRestore();
    mockRemoveChild.mockRestore();
    localStorage.removeItem("selectedCycleStartDate");
  });
});

describe("ButtonDownloadData", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the download button", () => {
    renderDownloadButton();
    expect(screen.getByRole("button", { name: /DOWNLOAD_DATA/i })).toBeInTheDocument();
  });

  it("clicking download button triggers GET and downloads file", async () => {
    const user = userEvent.setup();
    server.use(
      http.get("*/cycle-data/download-cycle_data", () =>
        HttpResponse.arrayBuffer(new ArrayBuffer(8))
      )
    );

    const mockCreateObjectURL = vi.fn().mockReturnValue("blob:http://localhost/data");
    const mockRevokeObjectURL = vi.fn();
    const mockClick = vi.fn();

    vi.stubGlobal("URL", { ...URL, createObjectURL: mockCreateObjectURL, revokeObjectURL: mockRevokeObjectURL });
    const createElementSpy = vi.spyOn(document, "createElement").mockImplementation((tag) => {
      const el = document.createElement.call(document, tag) as HTMLAnchorElement;
      if (tag === "a") el.click = mockClick;
      return el;
    });

    renderDownloadButton();
    await user.click(screen.getByRole("button", { name: /DOWNLOAD_DATA/i }));

    await waitFor(() => expect(mockCreateObjectURL).toHaveBeenCalled());
    expect(mockClick).toHaveBeenCalled();

    createElementSpy.mockRestore();
  });

  it("shows error toast when download fails", async () => {
    const user = userEvent.setup();
    server.use(
      http.get("*/cycle-data/download-cycle_data", () =>
        HttpResponse.json({ message: "error" }, { status: 500 })
      )
    );

    renderDownloadButton();
    await user.click(screen.getByRole("button", { name: /DOWNLOAD_DATA/i }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error" })
      )
    );
  });
});
