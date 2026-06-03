import { act, render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { server } from "../mocks/server";
import GoogleSheets from "features/cycle-detail/google-sheets/index";

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

const CYCLE_ID = "cycle-test-001";

function renderComponent() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/cycle/${CYCLE_ID}`]}>
        <Routes>
          <Route path="/cycle/:cycle_id" element={<GoogleSheets />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const disconnectedPayload = { payload: { is_active: false } };

function connectedPayload(overrides: Record<string, unknown> = {}) {
  return {
    payload: {
      is_active: true,
      last_status: "ok",
      spreadsheet_url: "https://docs.google.com/spreadsheets/d/sheet123/edit",
      last_synced: "2024-01-15T10:00:00Z",
      rows_synced: 42,
      last_error: null,
      ...overrides,
    },
  };
}

// ── Suite ──────────────────────────────────────────────────────────────────

describe("GoogleSheets", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
    vi.spyOn(window, "open").mockImplementation(() => null);
    server.use(
      http.get("*/sheets/sync-log", () =>
        HttpResponse.json({ message: "No sync log found for this cycle" }, { status: 404 })
      )
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
    if (vi.isFakeTimers()) vi.useRealTimers();
  });

  // ── Disconnected state ───────────────────────────────────────────────────

  describe("disconnected state", () => {
    beforeEach(() => {
      server.use(
        http.get("*/sheets/status", () => HttpResponse.json(disconnectedPayload))
      );
    });

    it("renders connect UI with Create Template button and ID/URL input", async () => {
      renderComponent();
      expect(await screen.findByText("Connect Google Sheets")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Create Template/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/Spreadsheet ID or URL/i)).toBeInTheDocument();
    });

    it("Connect button is disabled when input is empty", async () => {
      renderComponent();
      await screen.findByText("Connect Google Sheets");
      expect(screen.getByRole("button", { name: /^Connect$/i })).toBeDisabled();
    });

    it("Connect button enables once input has text", async () => {
      const user = userEvent.setup();
      renderComponent();
      await screen.findByText("Connect Google Sheets");
      await user.type(screen.getByLabelText(/Spreadsheet ID or URL/i), "abc123");
      expect(screen.getByRole("button", { name: /^Connect$/i })).toBeEnabled();
    });
  });

  // ── Connected states ─────────────────────────────────────────────────────

  describe("connected states", () => {
    it("shows an unavailable state when status request fails", async () => {
      server.use(
        http.get("*/sheets/status", () =>
          HttpResponse.json({ message: "Unauthorized" }, { status: 401 })
        )
      );
      renderComponent();
      expect(await screen.findByText("Google Sheets unavailable")).toBeInTheDocument();
      expect(screen.queryByText("Connect Google Sheets")).not.toBeInTheDocument();
    });

    it("shows Connected chip and Synced chip for ok status", async () => {
      server.use(
        http.get("*/sheets/status", () => HttpResponse.json(connectedPayload()))
      );
      renderComponent();
      expect(await screen.findByText("Connected")).toBeInTheDocument();
      expect(screen.getByText("Synced")).toBeInTheDocument();
      expect(screen.getByLabelText("Import mode")).toHaveTextContent("Import valid rows");
    });

    it("passes selected strict import mode to preview", async () => {
      const user = userEvent.setup();
      let importMode = "";
      server.use(
        http.get("*/sheets/status", () => HttpResponse.json(connectedPayload())),
        http.post("*/sheets/preview-sync", ({ request }) => {
          importMode = new URL(request.url).searchParams.get("import_mode") || "";
          return HttpResponse.json({
            payload: {
              preview_id: "preview-1",
              rows_valid: 1,
              rows_warning: 0,
              rows_error: 0,
              tab_summaries: [],
              rejected_rows: [],
            },
          });
        })
      );

      renderComponent();
      await screen.findByText("Connected");
      fireEvent.mouseDown(screen.getByLabelText("Import mode"));
      await user.click(screen.getByRole("option", { name: "Strict import" }));
      await user.click(screen.getByRole("button", { name: "Review & Sync" }));

      await screen.findByText("Review Import");
      expect(importMode).toBe("strict");
    });

    it("shows Partial chip for partial status", async () => {
      server.use(
        http.get("*/sheets/status", () =>
          HttpResponse.json(connectedPayload({ last_status: "partial" }))
        )
      );
      renderComponent();
      expect(await screen.findByText("Partial")).toBeInTheDocument();
    });

    it("shows queued status and sync id when a sync is queued", async () => {
      server.use(
        http.get("*/sheets/status", () =>
          HttpResponse.json(connectedPayload({
            last_status: "queued",
            active_sync_id: "sync-123",
          }))
        )
      );
      renderComponent();
      expect(await screen.findByText("Queued")).toBeInTheDocument();
      expect(screen.getByText("Sync ID: sync-123")).toBeInTheDocument();
    });

    it("loads sync log for the active sync id", async () => {
      let requestedSyncId = "";
      server.use(
        http.get("*/sheets/status", () =>
          HttpResponse.json(connectedPayload({
            last_status: "queued",
            active_sync_id: "sync-123",
          }))
        ),
        http.get("*/sheets/sync-log", ({ request }) => {
          requestedSyncId = new URL(request.url).searchParams.get("sync_id") || "";
          return HttpResponse.json({ message: "No sync log found for this sync" }, { status: 404 });
        })
      );

      renderComponent();
      await screen.findByText("Queued");
      await waitFor(() => expect(requestedSyncId).toBe("sync-123"));
    });

    it("shows access check failures and sync observability fields", async () => {
      server.use(
        http.get("*/sheets/status", () =>
          HttpResponse.json(connectedPayload({
            access_status: "error",
            access_error: "Spreadsheet permission denied",
            rows_per_second: 8.25,
            error_category: "google_auth",
          }))
        )
      );

      renderComponent();
      expect(await screen.findByText(/Spreadsheet access check failed/i)).toBeInTheDocument();
      expect(screen.getByText("Throughput: 8.25 rows/sec")).toBeInTheDocument();
      expect(screen.getByText("Error category: Google access")).toBeInTheDocument();
    });

    it("shows Error chip and inline error text for error status", async () => {
      server.use(
        http.get("*/sheets/status", () =>
          HttpResponse.json(
            connectedPayload({ last_status: "error", last_error: "API quota exceeded" })
          )
        )
      );
      renderComponent();
      expect(await screen.findByText("Error")).toBeInTheDocument();
      expect(screen.getByText("API quota exceeded")).toBeInTheDocument();
    });

    it("offers Review Again for stale preview errors", async () => {
      server.use(
        http.get("*/sheets/status", () =>
          HttpResponse.json(
            connectedPayload({
              last_status: "error",
              last_error: "Sheet changed since preview. Run preview-sync again.",
            })
          )
        )
      );
      renderComponent();
      expect(await screen.findByRole("button", { name: "Review Again" })).toBeInTheDocument();
    });

    it("shows no error text when last_status is not error", async () => {
      server.use(
        http.get("*/sheets/status", () => HttpResponse.json(connectedPayload()))
      );
      renderComponent();
      await screen.findByText("Connected");
      expect(screen.queryByText("API quota exceeded")).not.toBeInTheDocument();
    });

    it("renders spreadsheet link pointing to the sheet URL", async () => {
      server.use(
        http.get("*/sheets/status", () => HttpResponse.json(connectedPayload()))
      );
      renderComponent();
      const link = await screen.findByRole("link", { name: "Open Spreadsheet ↗" });
      expect(link).toHaveAttribute(
        "href",
        "https://docs.google.com/spreadsheets/d/sheet123/edit"
      );
    });
  });

  // ── Bug fix: auto-polling when status is syncing on mount ────────────────

  describe("auto-polling on mount when initial status is syncing", () => {
    it("sets syncing=true and shows Syncing… button text (proves startPolling was called)", async () => {
      server.use(
        http.get("*/sheets/status", () =>
          HttpResponse.json(connectedPayload({ last_status: "syncing" }))
        )
      );

      renderComponent();

      // Without the bug fix: button shows "Sync Now" (syncing=false, button disabled only by last_status)
      // With the bug fix: setSyncing(true) is called → button accessible name changes to "Syncing…"
      expect(
        await screen.findByRole("button", { name: /Syncing/i, hidden: true })
      ).toBeInTheDocument();
    });
  });

  // ── Connect by raw ID ────────────────────────────────────────────────────

  describe("connect with raw spreadsheet ID", () => {
    it("posts cycle_id + spreadsheet_id and transitions to connected UI", async () => {
      const user = userEvent.setup();
      let capturedBody: Record<string, string> = {};
      let statusCall = 0;

      server.use(
        http.get("*/sheets/status", () => {
          statusCall++;
          return HttpResponse.json(
            statusCall === 1 ? disconnectedPayload : connectedPayload()
          );
        }),
        http.post("*/sheets/connect", async ({ request }) => {
          capturedBody = (await request.json()) as Record<string, string>;
          return HttpResponse.json({});
        })
      );

      renderComponent();
      await screen.findByText("Connect Google Sheets");

      await user.type(screen.getByLabelText(/Spreadsheet ID or URL/i), "rawSheetId");
      await user.click(screen.getByRole("button", { name: /^Connect$/i }));

      expect(await screen.findByText("Connected")).toBeInTheDocument();
      expect(capturedBody.cycle_id).toBe(CYCLE_ID);
      expect(capturedBody.spreadsheet_id).toBe("rawSheetId");
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "Google Sheets connected" })
      );
    });
  });

  // ── Connect by URL (ID extraction) ───────────────────────────────────────

  describe("connect with full Google Sheets URL", () => {
    it("extracts the spreadsheet ID from the URL before POSTing", async () => {
      const user = userEvent.setup();
      let capturedSpreadsheetId = "";
      let statusCall = 0;

      server.use(
        http.get("*/sheets/status", () => {
          statusCall++;
          return HttpResponse.json(
            statusCall === 1 ? disconnectedPayload : connectedPayload()
          );
        }),
        http.post("*/sheets/connect", async ({ request }) => {
          const body = (await request.json()) as Record<string, string>;
          capturedSpreadsheetId = body.spreadsheet_id;
          return HttpResponse.json({});
        })
      );

      renderComponent();
      await screen.findByText("Connect Google Sheets");

      const url = "https://docs.google.com/spreadsheets/d/extracted-id-789/edit#gid=0";
      await user.type(screen.getByLabelText(/Spreadsheet ID or URL/i), url);
      await user.click(screen.getByRole("button", { name: /^Connect$/i }));

      await waitFor(() => expect(capturedSpreadsheetId).toBe("extracted-id-789"));
    });
  });

  // ── Connect failure ───────────────────────────────────────────────────────

  describe("connect failure", () => {
    it("shows error toast when connect API returns an error", async () => {
      const user = userEvent.setup();

      server.use(
        http.get("*/sheets/status", () => HttpResponse.json(disconnectedPayload)),
        http.post("*/sheets/connect", () =>
          HttpResponse.json({ message: "Cannot access sheet" }, { status: 400 })
        )
      );

      renderComponent();
      await screen.findByText("Connect Google Sheets");
      await user.type(screen.getByLabelText(/Spreadsheet ID or URL/i), "badId");
      await user.click(screen.getByRole("button", { name: /^Connect$/i }));

      await waitFor(() =>
        expect(mockSetToast).toHaveBeenCalledWith(
          expect.objectContaining({ variant: "error" })
        )
      );
      // UI stays on disconnected screen — no transition
      expect(screen.getByText("Connect Google Sheets")).toBeInTheDocument();
    });
  });

  // ── Create template ───────────────────────────────────────────────────────

  describe("create template", () => {
    it("calls create-template, opens new tab, transitions to connected UI", async () => {
      const user = userEvent.setup();
      let statusCall = 0;

      server.use(
        http.get("*/sheets/status", () => {
          statusCall++;
          return HttpResponse.json(
            statusCall === 1 ? disconnectedPayload : connectedPayload()
          );
        }),
        http.post("*/sheets/create-template", () =>
          HttpResponse.json({
            payload: {
              spreadsheet_url: "https://docs.google.com/spreadsheets/d/new-sheet/edit",
            },
          })
        )
      );

      renderComponent();
      await screen.findByText("Connect Google Sheets");
      await user.click(screen.getByRole("button", { name: /Create Template/i }));

      expect(await screen.findByText("Connected")).toBeInTheDocument();
      expect(window.open).toHaveBeenCalledWith(
        "https://docs.google.com/spreadsheets/d/new-sheet/edit",
        "_blank"
      );
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({
          variant: "success",
          text: "Template created and connected",
        })
      );
    });
  });

  // ── Manual sync + polling state machine ──────────────────────────────────

  describe("manual sync polling", () => {
    // Use real timers for initial render, then fake timers for polling control.
    // The poll timer is created by startPolling() AFTER we switch to fake timers,
    // so vi.advanceTimersByTimeAsync correctly controls it.

    it("resolves to ok: shows Synced chip and success toast", async () => {
      let statusCall = 0;
      server.use(
        http.get("*/sheets/status", () => {
          statusCall++;
          // 1: initial load → ok; 2: first poll → syncing; 3+: second poll → ok
          const status = statusCall === 1 ? "ok" : statusCall === 2 ? "syncing" : "ok";
          return HttpResponse.json(connectedPayload({ last_status: status }));
        }),
        http.post("*/sheets/manual-sync", () => HttpResponse.json({}))
      );

      renderComponent();
      const syncBtn = await screen.findByRole("button", { name: /Sync Now/i });

      // Switch to fake timers AFTER initial load so that startPolling's
      // setTimeout calls are captured as fake timers.
      vi.useFakeTimers();
      fireEvent.click(syncBtn);

      await act(() => vi.advanceTimersByTimeAsync(3000)); // poll #1 → syncing, schedules poll #2
      await act(() => vi.advanceTimersByTimeAsync(3000)); // poll #2 → ok, clears syncing

      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "Sync complete" })
      );
    });

    it("resolves to error: shows error toast with message", async () => {
      let statusCall = 0;
      server.use(
        http.get("*/sheets/status", () => {
          statusCall++;
          if (statusCall === 1) return HttpResponse.json(connectedPayload());
          return HttpResponse.json(
            connectedPayload({ last_status: "error", last_error: "Sheet not found" })
          );
        }),
        http.post("*/sheets/manual-sync", () => HttpResponse.json({}))
      );

      renderComponent();
      const syncBtn = await screen.findByRole("button", { name: /Sync Now/i });

      vi.useFakeTimers();
      fireEvent.click(syncBtn);

      await act(() => vi.advanceTimersByTimeAsync(3000)); // poll #1 → error

      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({
          variant: "error",
          text: expect.stringContaining("Sheet not found"),
        })
      );
    });

    it("resolves to partial: shows warning toast", async () => {
      let statusCall = 0;
      server.use(
        http.get("*/sheets/status", () => {
          statusCall++;
          if (statusCall === 1) return HttpResponse.json(connectedPayload());
          return HttpResponse.json(connectedPayload({ last_status: "partial" }));
        }),
        http.post("*/sheets/manual-sync", () => HttpResponse.json({}))
      );

      renderComponent();
      const syncBtn = await screen.findByRole("button", { name: /Sync Now/i });

      vi.useFakeTimers();
      fireEvent.click(syncBtn);

      await act(() => vi.advanceTimersByTimeAsync(3000)); // poll #1 → partial

      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({
          variant: "warning",
          text: "Sync finished with some errors — check issues below",
        })
      );
    });

    it("times out after 20 attempts still syncing: shows 'taking longer' toast", async () => {
      let statusCall = 0;
      server.use(
        http.get("*/sheets/status", () => {
          statusCall++;
          // First call: ok (so Sync Now button is enabled and readable)
          // All subsequent calls: still syncing (simulates a stuck sync)
          if (statusCall === 1) return HttpResponse.json(connectedPayload({ last_status: "ok" }));
          return HttpResponse.json(connectedPayload({ last_status: "syncing" }));
        }),
        http.post("*/sheets/manual-sync", () => HttpResponse.json({}))
      );

      renderComponent();
      const syncBtn = await screen.findByRole("button", { name: /Sync Now/i });

      vi.useFakeTimers();
      fireEvent.click(syncBtn);
      await act(() => vi.advanceTimersByTimeAsync(0));

      for (let i = 0; i < 20; i++) {
        await act(() => vi.advanceTimersByTimeAsync(3000));
      }

      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ text: "Sync is taking longer than expected" })
      );
    }, 15000);
  });

  // ── Disconnect ────────────────────────────────────────────────────────────

  describe("disconnect", () => {
    it("calls disconnect endpoint and returns to disconnected UI", async () => {
      const user = userEvent.setup();
      let statusCall = 0;

      server.use(
        http.get("*/sheets/status", () => {
          statusCall++;
          return HttpResponse.json(
            statusCall === 1 ? connectedPayload() : disconnectedPayload
          );
        }),
        http.delete("*/sheets/disconnect", () => HttpResponse.json({}))
      );

      renderComponent();
      await screen.findByText("Connected");

      await user.click(screen.getByRole("button", { name: /Disconnect/i }));

      expect(await screen.findByText("Connect Google Sheets")).toBeInTheDocument();
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "Disconnected" })
      );
    });
  });
});
