import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { server } from "../mocks/server";
import PondMemoryPanel from "components/pond-memory-panel";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => mockNavigate };
});

function renderComponent() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <PondMemoryPanel farmId="farm-1" pondId="pond-1" pondName="Pond One" />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("PondMemoryPanel", () => {
  it("renders recent pond memories and navigates to memory management", async () => {
    const user = userEvent.setup();

    server.use(
      http.get("*/agent/memories", () =>
        HttpResponse.json({
          payload: {
            memories: [
              {
                id: "memory-1",
                memory_type: "event",
                content: "Pond One had low DO after overnight rain.",
                tags: ["do"],
                farm_id: "farm-1",
                pond_id: "pond-1",
                cycle_id: "cycle-1",
                source: "user_input",
                is_verified: true,
                created_at: "2026-01-01T00:00:00",
              },
            ],
          },
        })
      )
    );

    renderComponent();

    expect(await screen.findByText("Pond One had low DO after overnight rain.")).toBeInTheDocument();
    expect(screen.getByText("Remembered context for Pond One.")).toBeInTheDocument();
    expect(screen.getByText("Issues & Events")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Manage memory" }));

    expect(mockNavigate).toHaveBeenCalledWith("/dashboard/memory");
  });

  it("shows an empty state when no pond memories exist", async () => {
    server.use(
      http.get("*/agent/memories", () => HttpResponse.json({ payload: { memories: [] } }))
    );

    renderComponent();

    expect(await screen.findByText("No pond-specific memories yet. Add facts, events, or outcomes from the Memory page.")).toBeInTheDocument();
  });
});
