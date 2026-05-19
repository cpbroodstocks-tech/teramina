import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { server } from "../mocks/server";
import AgentChat from "components/agent-chat";

const mockSetToast = vi.fn();
const agentChatProps = {
  open: true,
  onClose: vi.fn(),
  onAlertsLoaded: undefined,
  initialMessage: "",
  onInitialMessageConsumed: undefined,
};

vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: mockSetToast }),
}));

function renderComponent(initialEntry = "/assistant") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/assistant" element={<AgentChat {...agentChatProps} />} />
          <Route path="/dashboard/pond-timeline/:cycle_id" element={<AgentChat {...agentChatProps} />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

function streamResponse(chunks: string[]) {
  const encoder = new TextEncoder();
  return new Response(
    new ReadableStream({
      start(controller) {
        chunks.forEach((chunk) => controller.enqueue(encoder.encode(chunk)));
        controller.close();
      },
    }),
    { status: 200, headers: { "Content-Type": "text/event-stream" } }
  );
}

describe("AgentChat", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
    localStorage.setItem("authentication", "test-token");
    localStorage.setItem("farm_id", "farm-1");
    localStorage.setItem("pond_id", "pond-1");
    localStorage.setItem("cycle_id", "cycle-1");
    Element.prototype.scrollIntoView = vi.fn();
    server.use(
      http.get("*/agent/alerts", () => HttpResponse.json({ payload: { alerts: [] } })),
      http.get("*/agent/tasks", () => HttpResponse.json({ payload: { tasks: [] } })),
      http.get("*/agent/history", () => HttpResponse.json({ payload: { messages: [] } }))
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("streams a response with current farm, pond, and cycle context", async () => {
    const user = userEvent.setup();
    let capturedBody: Record<string, unknown> = {};

    vi.spyOn(window, "fetch").mockImplementation(async (_input, init) => {
      capturedBody = JSON.parse(String(init?.body || "{}"));
      return streamResponse([
        "data: {\"type\":\"text\",\"delta\":\"Recommendation: Check aeration.\"}\n\n",
        "data: {\"type\":\"done\",\"session_id\":\"session-1\"}\n\n",
      ]);
    });

    renderComponent();

    await user.type(screen.getByPlaceholderText("Ask about your farm…"), "Why is DO low?{enter}");

    await screen.findByText("Recommendation: Check aeration.");
    await waitFor(() => expect(capturedBody.message).toBe("Why is DO low?"));
    expect(capturedBody.farm_id).toBe("farm-1");
    expect(capturedBody.pond_id).toBe("pond-1");
    expect(capturedBody.cycle_id).toBe("cycle-1");
    expect(capturedBody.page_context).toEqual({
      route: "/assistant",
      page_type: "unknown",
      farm_id: "farm-1",
      pond_id: "pond-1",
      cycle_id: "cycle-1",
      filters: {},
    });
    expect(localStorage.getItem("agent_session_id")).toBe("session-1");
  });

  it("prioritizes route and query context over localStorage", async () => {
    const user = userEvent.setup();
    let capturedBody: Record<string, unknown> = {};

    vi.spyOn(window, "fetch").mockImplementation(async (_input, init) => {
      capturedBody = JSON.parse(String(init?.body || "{}"));
      return streamResponse([
        "data: {\"type\":\"text\",\"delta\":\"Route context received.\"}\n\n",
        "data: {\"type\":\"done\",\"session_id\":\"session-route\"}\n\n",
      ]);
    });

    renderComponent("/dashboard/pond-timeline/cycle-url?farm_id=farm-url&pond_id=pond-url&status=active");

    await user.type(screen.getByPlaceholderText("Ask about your farm…"), "What happened here?{enter}");

    await screen.findByText("Route context received.");
    expect(capturedBody.farm_id).toBe("farm-url");
    expect(capturedBody.pond_id).toBe("pond-url");
    expect(capturedBody.cycle_id).toBe("cycle-url");
    expect(capturedBody.page_context).toEqual({
      route: "/dashboard/pond-timeline/cycle-url",
      page_type: "pond_timeline",
      farm_id: "farm-url",
      pond_id: "pond-url",
      cycle_id: "cycle-url",
      filters: { status: "active" },
    });
  });

  it("asks for confirmation before saving a memory from chat", async () => {
    const user = userEvent.setup();
    let capturedMemory: Record<string, unknown> = {};
    const fetchSpy = vi.spyOn(window, "fetch").mockResolvedValue(streamResponse([]));

    server.use(
      http.post("*/agent/memories", async ({ request }) => {
        capturedMemory = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ payload: { id: "memory-1" } });
      })
    );

    renderComponent("/dashboard/pond-timeline/cycle-url?farm_id=farm-url&pond_id=pond-url");

    await user.type(screen.getByPlaceholderText("Ask about your farm…"), "Remember Pond B has low DO after rain{enter}");

    expect(await screen.findByText(/Should I remember this for future recommendations/i)).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
    await user.clear(screen.getByLabelText("Edit memory before saving"));
    await user.type(screen.getByLabelText("Edit memory before saving"), "Pond B has recurring low DO after heavy rain");

    await user.click(screen.getByRole("button", { name: "Remember" }));

    await screen.findByText("Remembered: Pond B has recurring low DO after heavy rain");
    expect(capturedMemory).toMatchObject({
      farm_id: "farm-url",
      pond_id: "pond-url",
      cycle_id: "cycle-url",
      memory_type: "note",
      content: "Pond B has recurring low DO after heavy rain",
      tags: ["chat_confirmation"],
      confidence: 0.9,
    });
  });
});
