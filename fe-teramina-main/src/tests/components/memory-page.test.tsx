import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { server } from "../mocks/server";
import MemoryPage from "pages/dashboard/memory";
import { useDashboardContextStore } from "store/dashboard-context.store";

const mockSetToast = vi.fn();
vi.mock("store/toast.store", () => ({
  useToastStore: () => ({ setToast: mockSetToast }),
}));

function renderComponent() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <MemoryPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const memoryPayload = {
  payload: {
    memories: [
      {
        id: "memory-1",
        memory_type: "preference",
        content: "Farmer prefers harvest around size 40.",
        tags: ["harvest"],
        farm_id: "farm-1",
        pond_id: "pond-1",
        cycle_id: "",
        source: "user_input",
        is_verified: true,
        created_at: "2026-01-01T00:00:00",
      },
    ],
  },
};

const graphPayload = {
  payload: {
    entities: [
      {
        id: "entity-1",
        entity_type: "pond",
        canonical_name: "pond:pond-1",
        farm_id: "farm-1",
        metadata: {},
      },
    ],
    relations: [
      {
        id: "relation-1",
        source_entity_id: "entity-1",
        relation_type: "mentions",
        target_entity_id: "entity-2",
        confidence: 0.8,
        source_type: "farmer",
      },
    ],
    observations: [
      {
        id: "observation-1",
        entity_id: "entity-1",
        observation_type: "preference",
        content: "Graph remembers harvest preference for Pond One.",
        farm_id: "farm-1",
        pond_id: "pond-1",
        cycle_id: "",
        confidence: 0.9,
        source_type: "farmer",
        is_verified: true,
        created_at: "2026-01-01T00:00:00",
      },
    ],
  },
};

describe("MemoryPage", () => {
  beforeEach(() => {
    mockSetToast.mockClear();
    useDashboardContextStore.getState().setContext({
      farm_id: "farm-1",
      pond_id: "pond-1",
      farm_name: "Farm One",
      pond_name: "Pond One",
    });
  });

  it("renders existing memories from /agent/memories", async () => {
    server.use(
      http.get("*/agent/memories", () => HttpResponse.json(memoryPayload)),
      http.get("*/agent/memories/graph", () => HttpResponse.json(graphPayload))
    );

    renderComponent();

    expect(await screen.findByText("Farmer prefers harvest around size 40.")).toBeInTheDocument();
    expect(screen.getAllByText("preference")[0]).toBeInTheDocument();
    expect(screen.getByText("Graph remembers harvest preference for Pond One.")).toBeInTheDocument();
    expect(screen.getByText("1 entities")).toBeInTheDocument();
    expect(screen.getByText("1 links")).toBeInTheDocument();
    expect(screen.getByText("1 observations")).toBeInTheDocument();
  });

  it("posts a new contextual memory and shows success toast", async () => {
    const user = userEvent.setup();
    let capturedBody: Record<string, unknown> = {};

    server.use(
      http.get("*/agent/memories", () => HttpResponse.json({ payload: { memories: [] } })),
      http.get("*/agent/memories/graph", () =>
        HttpResponse.json({ payload: { entities: [], relations: [], observations: [] } })
      ),
      http.post("*/agent/memories", async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ payload: { id: "new-memory" } });
      })
    );

    renderComponent();
    await user.type(screen.getByLabelText("What should Teramina remember?"), "Pond A responds well to aeration.");
    await user.type(screen.getByLabelText("Tags"), "do, aeration");
    await user.click(screen.getByRole("button", { name: /^Save memory$/i }));

    await waitFor(() =>
      expect(mockSetToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "success", text: "Memory saved" })
      )
    );
    expect(capturedBody.farm_id).toBe("farm-1");
    expect(capturedBody.pond_id).toBe("pond-1");
    expect(capturedBody.tags).toEqual(["do", "aeration"]);
  });

  it("deletes a memory and refreshes the list", async () => {
    const user = userEvent.setup();
    let deletedId = "";

    server.use(
      http.get("*/agent/memories", () => HttpResponse.json(memoryPayload)),
      http.get("*/agent/memories/graph", () => HttpResponse.json(graphPayload)),
      http.delete("*/agent/memories/:id", ({ params }) => {
        deletedId = String(params.id);
        return HttpResponse.json({ payload: {} });
      })
    );

    renderComponent();
    expect(await screen.findByText("Farmer prefers harvest around size 40.")).toBeInTheDocument();
    await user.click(screen.getByTitle("Delete memory"));

    await waitFor(() => expect(deletedId).toBe("memory-1"));
  });

  it("updates a corrected memory and shows success toast", async () => {
    const user = userEvent.setup();
    let updatedId = "";
    let capturedBody: Record<string, unknown> = {};

    server.use(
      http.get("*/agent/memories", () => HttpResponse.json(memoryPayload)),
      http.get("*/agent/memories/graph", () => HttpResponse.json(graphPayload)),
      http.patch("*/agent/memories/:id", async ({ params, request }) => {
        updatedId = String(params.id);
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ payload: { id: updatedId } });
      })
    );

    renderComponent();
    expect(await screen.findByText("Farmer prefers harvest around size 40.")).toBeInTheDocument();

    await user.click(screen.getByTitle("Correct memory"));
    await user.clear(screen.getByLabelText("Correct memory"));
    await user.type(screen.getByLabelText("Correct memory"), "Farmer prefers harvest around size 35.");
    await user.click(screen.getByTitle("Save correction"));

    await waitFor(() => expect(updatedId).toBe("memory-1"));
    expect(capturedBody).toMatchObject({
      memory_type: "preference",
      content: "Farmer prefers harvest around size 35.",
      tags: ["harvest"],
      confidence: 0.95,
    });
    expect(mockSetToast).toHaveBeenCalledWith(expect.objectContaining({ variant: "success", text: "Memory updated" }));
  });
});
