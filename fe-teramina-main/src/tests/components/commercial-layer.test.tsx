import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "../mocks/server";
import { DashboardAdvisoryDetailPage } from "features/advisory/dashboard-pages";
import { AdvisoryIntakePage, ServicesPage } from "features/advisory/public-pages";
import DashboardBillingPage from "features/billing/dashboard-page";
import { ContentDetailPage, KnowledgePage } from "features/content/public-pages";
import CommercialAdminPage from "features/commercial-admin/page";

function renderWithProviders(component: React.ReactElement, initialEntries = ["/"]) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>{component}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Commercial public surfaces", () => {
  it("renders advisory service packages from the API", async () => {
    localStorage.removeItem("authentication");
    server.use(
      http.get("*/advisory/packages", () =>
        HttpResponse.json({
          payload: {
            packages: [
              {
                id: "pkg-1",
                name: "Farm Diagnostic Review",
                slug: "farm-diagnostic-review",
                segment: "farm",
                description: "Structured technical review",
                deliverables: ["Cause ranking"],
                required_data: ["Water quality logs"],
                price_min_idr: 3000000,
                price_max_idr: 10000000,
              },
            ],
          },
        })
      )
    );

    renderWithProviders(<ServicesPage />);

    expect(await screen.findByText("Farm Diagnostic Review")).toBeInTheDocument();
    expect(screen.getByText("Structured technical review")).toBeInTheDocument();
  });

  it("renders knowledge items and locked paid detail state", async () => {
    localStorage.removeItem("authentication");
    server.use(
      http.get("*/content/items", () =>
        HttpResponse.json({
          payload: {
            items: [
              {
                id: "content-1",
                title: "Broodstock SOP",
                slug: "broodstock-sop",
                summary: "Receiving and quarantine",
                category: "Hatchery",
                tags: ["broodstock"],
                access_level: "paid",
                access_status: "locked",
                language: "en",
                variant_type: "master",
              },
            ],
          },
        })
      ),
      http.get("*/content/items/broodstock-sop", () =>
        HttpResponse.json({
          payload: {
            item: {
              id: "content-1",
              title: "Broodstock SOP",
              slug: "broodstock-sop",
              summary: "Receiving and quarantine",
              category: "Hatchery",
              tags: ["broodstock"],
              access_level: "paid",
              access_status: "locked",
              language: "en",
              variant_type: "master",
            },
          },
        })
      )
    );

    renderWithProviders(<KnowledgePage />);
    expect(await screen.findByText("Broodstock SOP")).toBeInTheDocument();

    renderWithProviders(
      <Routes>
        <Route path="/knowledge/:slug" element={<ContentDetailPage />} />
      </Routes>,
      ["/knowledge/broodstock-sop"]
    );

    expect(await screen.findByText("This material requires paid or client access. Manual access is granted after purchase or advisory engagement.")).toBeInTheDocument();
  });

  it("shows PDF download for unlocked content detail", async () => {
    localStorage.removeItem("authentication");
    server.use(
      http.get("*/content/items/farm-guide", () =>
        HttpResponse.json({
          payload: {
            item: {
              id: "content-free",
              title: "Farm Guide",
              slug: "farm-guide",
              summary: "Free guide",
              category: "Farm",
              access_level: "free",
              access_status: "free",
              language: "id",
              variant_type: "practical",
              body_markdown: "Full guide body",
            },
          },
        })
      )
    );

    renderWithProviders(
      <Routes>
        <Route path="/knowledge/:slug" element={<ContentDetailPage />} />
      </Routes>,
      ["/knowledge/farm-guide"]
    );

    expect(await screen.findByText("Full guide body")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download PDF" })).toBeInTheDocument();
  });

  it("submits structured farm diagnostic intake", async () => {
    localStorage.setItem("authentication", "test-token");
    let submittedPayload: any = null;
    server.use(
      http.get("*/advisory/packages/farm-diagnostic-review", () =>
        HttpResponse.json({
          payload: {
            package: {
              id: "pkg-1",
              name: "Farm Diagnostic Review",
              slug: "farm-diagnostic-review",
              segment: "farm",
              description: "Structured technical review",
            },
          },
        })
      ),
      http.post("*/advisory/cases", async ({ request }) => {
        submittedPayload = await request.json();
        return HttpResponse.json({
          payload: {
            case: {
              id: "case-123",
              title: submittedPayload.title,
              case_type: submittedPayload.case_type,
              status: "inquiry",
            },
          },
        });
      })
    );

    renderWithProviders(
      <Routes>
        <Route path="/advisory/intake/:service_slug" element={<AdvisoryIntakePage />} />
      </Routes>,
      ["/advisory/intake/farm-diagnostic-review"]
    );

    expect(await screen.findByText("Farm Diagnostic Review")).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText(/Farm name and location/), "Tambak A, Lampung");
    await userEvent.type(screen.getByLabelText(/Stocking date/), "2026-05-01");
    await userEvent.type(screen.getByLabelText(/Main question or problem/), "FCR increased after DOC 50");
    await userEvent.click(screen.getByRole("button", { name: "Submit Advisory Case" }));

    expect(await screen.findByText("Advisory case submitted. Case ID: case-123")).toBeInTheDocument();
    expect(submittedPayload.case_type).toBe("farm_diagnostic");
    expect(submittedPayload.intake_data.farm_name_location).toBe("Tambak A, Lampung");
    expect(submittedPayload.intake_data.main_question).toBe("FCR increased after DOC 50");
  }, 10000);

  it("renders advisory case detail with structured intake and delivered report", async () => {
    server.use(
      http.get("*/advisory/cases/case-1", () =>
        HttpResponse.json({
          payload: {
            case: {
              id: "case-1",
              title: "Weak FCR review",
              case_type: "farm_diagnostic",
              status: "report_ready",
              created_at: "2026-05-01T00:00:00",
              intake_data: {
                farm_name_location: "Tambak A, Lampung",
                main_question: "FCR increased after DOC 50",
              },
              uploaded_files: [
                {
                  name: "Water quality log",
                  url: "https://storage.example/private/wq-log.csv",
                  description: "DOC 1-50 export",
                },
              ],
            },
            expert_reviews: [
              {
                id: "review-1",
                review_type: "disease",
                status: "delivered",
                summary: "Disease pressure is plausible but unconfirmed.",
                findings: ["Mortality timeline accelerates after DOC 42"],
                recommendations: ["Run PCR confirmation before restart"],
                next_actions: ["Collect pond-edge shrimp sample"],
              },
            ],
            retainer_cadences: [
              {
                id: "cadence-1",
                cadence_type: "biweekly",
                status: "active",
                next_review_at: "2026-05-15T00:00:00",
                agenda: ["Review feed curve"],
                notes: "Prepare latest pond logs before the call.",
              },
            ],
            report: {
              id: "report-1",
              title: "Diagnostic Report",
              executive_summary: "Likely oxygen pressure issue.",
              key_findings: ["Oxygen risk increased after biomass passed 2 tons"],
              corrective_action_plan: ["Increase night aeration review"],
              status: "delivered",
            },
          },
        })
      )
    );

    renderWithProviders(
      <Routes>
        <Route path="/dashboard/advisory/:case_id" element={<DashboardAdvisoryDetailPage />} />
      </Routes>,
      ["/dashboard/advisory/case-1"]
    );

    expect(await screen.findByText("Weak FCR review")).toBeInTheDocument();
    expect(screen.getByText("Tambak A, Lampung")).toBeInTheDocument();
    expect(screen.getByText("Diagnostic Report")).toBeInTheDocument();
    expect(screen.getByText("Likely oxygen pressure issue.")).toBeInTheDocument();
    expect(screen.getByText("Oxygen risk increased after biomass passed 2 tons")).toBeInTheDocument();
    expect(screen.getByText("Water quality log")).toBeInTheDocument();
    expect(screen.getByText("Disease pressure is plausible but unconfirmed.")).toBeInTheDocument();
    expect(screen.getByText("Review feed curve")).toBeInTheDocument();
  });

  it("renders user invoices in dashboard billing", async () => {
    server.use(
      http.get("*/billing/my-invoices", () =>
        HttpResponse.json({
          payload: {
            invoices: [
              {
                id: "invoice-1",
                invoice_number: "INV-001",
                invoice_type: "content_access",
                status: "paid",
                description: "Paid library access",
                amount_idr: 500000,
                issued_at: "2026-05-01T00:00:00",
                paid_at: "2026-05-02T00:00:00",
                payment_method: "manual_transfer",
              },
            ],
          },
        })
      )
    );

    renderWithProviders(<DashboardBillingPage />);

    expect(await screen.findByText("INV-001")).toBeInTheDocument();
    expect(screen.getByText("Paid library access")).toBeInTheDocument();
    expect(screen.getByText("Rp 500.000")).toBeInTheDocument();
  });
});

describe("Commercial admin surface", () => {
  it("renders admin workflow controls for admin users", async () => {
    let acceptedLogId = "";
    let draftReportLogId = "";
    let reportWorkflowId = "";

    server.use(
      http.get("*/user/get-profile", () =>
        HttpResponse.json({
          payload: { name: "Admin", email: "admin@teramina.com", role_user: "admin" },
        })
      ),
      http.get("*/content/admin/items", () =>
        HttpResponse.json({
          payload: {
            items: [
              {
                id: "content-1",
                title: "Broodstock SOP",
                slug: "broodstock-sop",
                status: "published",
                access_level: "paid",
              },
            ],
          },
        })
      ),
      http.get("*/content/admin/access", () =>
        HttpResponse.json({
          payload: { access: [] },
        })
      ),
      http.get("*/content/admin/items/content-1", () =>
        HttpResponse.json({
          payload: {
            item: {
              id: "content-1",
              title: "Broodstock SOP",
              slug: "broodstock-sop",
              summary: "Receiving and quarantine",
              category: "Hatchery",
              tags: ["broodstock"],
              language: "en",
              variant_group_id: "broodstock-sop",
              variant_type: "master",
              source_content_id: "",
              content_type: "sop",
              access_level: "paid",
              status: "published",
              version: "1.1",
              body_markdown: "Updated SOP body",
              review_notes: "Approved for release",
            },
          },
        })
      ),
      http.get("*/content/admin/items/content-1/revisions", () =>
        HttpResponse.json({
          payload: {
            revisions: [
              {
                id: "rev-2",
                revision_number: 2,
                version: "1.1",
                status: "published",
                change_note: "Reviewed thresholds",
                created_at: "2026-05-01T00:00:00",
              },
            ],
          },
        })
      ),
      http.get("*/advisory/admin/cases", () =>
        HttpResponse.json({
          payload: {
            cases: [
              {
                id: "case-1",
                title: "Weak FCR review",
                case_type: "farm_diagnostic",
                status: "inquiry",
                user_id: "user-1",
                intake_data: { main_problem: "FCR increased" },
              },
            ],
          },
        })
      ),
      http.get("*/advisory/admin/cases/case-1/assistant-brief", () =>
        HttpResponse.json({
          payload: {
            brief: {
              brief_log_id: "log-1",
              case: { id: "case-1", title: "Weak FCR review" },
              missing_data: ["Disease Test Results"],
              uploaded_file_checks: {
                total_files: 1,
                passed: 1,
                needs_review: 0,
                checks: [],
              },
              reference_documents: [
                {
                  id: "content-1",
                  title: "Farm Failure Framework",
                  category: "Farm",
                  language: "en",
                },
              ],
              draft_report: {
                title: "Assistant Draft: Weak FCR review",
                executive_summary: "Internal first-pass brief for weak FCR review.",
                key_findings: ["Check PCR result availability"],
                corrective_action_plan: ["Request missing disease test result"],
              },
            },
          },
        })
      ),
      http.post("*/advisory/admin/assistant-brief-logs/log-1/accept", () => {
        acceptedLogId = "log-1";
        return HttpResponse.json({
          payload: {
            brief_log: {
              id: "log-1",
              status: "accepted",
            },
          },
        });
      }),
      http.post("*/advisory/admin/assistant-brief-logs/log-1/draft-report", () => {
        draftReportLogId = "log-1";
        return HttpResponse.json({
          payload: {
            report: {
              id: "report-draft-1",
              status: "expert_review_required",
            },
          },
        });
      }),
      http.get("*/advisory/admin/expert-reviews", () =>
        HttpResponse.json({
          payload: {
            reviews: [
              {
                id: "review-1",
                case_id: "case-1",
                review_type: "technical",
                status: "delivered",
              },
            ],
          },
        })
      ),
      http.get("*/advisory/admin/reports", () =>
        HttpResponse.json({
          payload: {
            reports: [
              {
                id: "report-draft-1",
                case_id: "case-1",
                title: "Assistant Draft: Weak FCR review",
                status: "expert_review_required",
              },
            ],
          },
        })
      ),
      http.patch("*/advisory/admin/reports/report-draft-1/workflow", async ({ request }) => {
        const payload = await request.json() as { status: string };
        reportWorkflowId = `report-draft-1:${payload.status}`;
        return HttpResponse.json({
          payload: {
            report: {
              id: "report-draft-1",
              status: payload.status,
            },
            case: {
              id: "case-1",
              status: "report_ready",
            },
          },
        });
      }),
      http.get("*/advisory/admin/retainer-cadences", () =>
        HttpResponse.json({
          payload: {
            cadences: [
              {
                id: "cadence-1",
                case_id: "case-1",
                cadence_type: "monthly",
                status: "active",
                next_review_at: "2026-05-15T00:00:00",
              },
            ],
          },
        })
      ),
      http.get("*/billing/admin/invoices", () =>
        HttpResponse.json({
          payload: {
            invoices: [
              {
                id: "invoice-1",
                invoice_number: "INV-001",
                user_id: "user-1",
                status: "issued",
                amount_idr: 500000,
              },
            ],
          },
        })
      )
    );

    renderWithProviders(<CommercialAdminPage />);

    expect(await screen.findByText("Commercial Admin")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Create Content" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Content Operations" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Editorial Workflow" })).toBeInTheDocument();
    expect(screen.getByText("Grant Library Access")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Create Invoice" })).toBeInTheDocument();
    expect(await screen.findByText("Revision 2", {}, { timeout: 5000 })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getAllByText("Weak FCR review").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Assistant Brief")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Generate Assistant Brief" }));
    expect(await screen.findByText("Check PCR result availability")).toBeInTheDocument();
    expect(screen.getByText("Farm Failure Framework (Farm, en)")).toBeInTheDocument();
    expect(screen.getByText("Files: 1")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Use Draft In Report Form" }));
    await waitFor(() => expect(acceptedLogId).toBe("log-1"));
    await userEvent.click(screen.getByRole("button", { name: "Create Internal Draft Report" }));
    await waitFor(() => expect(draftReportLogId).toBe("log-1"));
    await userEvent.click(screen.getByRole("button", { name: "Update Report Workflow" }));
    await waitFor(() => expect(reportWorkflowId).toBe("report-draft-1:delivered"));
    expect(screen.getByText("Expert Review Forms")).toBeInTheDocument();
    expect(screen.getByText("Retainer Cadence")).toBeInTheDocument();
    expect(screen.getByText("Deliver Report")).toBeInTheDocument();
  }, 10000);

  it("blocks commercial admin page for non-admin users", async () => {
    server.use(
      http.get("*/user/get-profile", () =>
        HttpResponse.json({
          payload: { name: "Member", email: "member@teramina.com", role_user: "member" },
        })
      )
    );

    renderWithProviders(<CommercialAdminPage />);

    expect(await screen.findByText("Commercial admin is available only to admin users.")).toBeInTheDocument();
  });
});
