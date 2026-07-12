import { beforeEach, describe, expect, it, vi } from "vitest";

const axiosMock = vi.hoisted(() => {
  const requestHandlers: Array<(config: Record<string, unknown>) => Record<string, unknown>> = [];
  const responseErrorHandlers: Array<(error: Record<string, any>) => Promise<unknown>> = [];
  const instance = Object.assign(vi.fn(), {
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn((handler) => requestHandlers.push(handler)) },
      response: { use: vi.fn((_success, error) => responseErrorHandlers.push(error)) },
    },
  });

  return { create: vi.fn(() => instance), instance, requestHandlers, responseErrorHandlers };
});

vi.mock("axios", () => ({ default: { create: axiosMock.create } }));
vi.mock("firebase/auth", () => ({ getAuth: vi.fn(), signOut: vi.fn().mockResolvedValue(undefined) }));

describe("Axios authentication interceptor", () => {
  beforeEach(async () => {
    localStorage.clear();
    axiosMock.instance.mockReset();
    axiosMock.instance.get.mockReset();
    vi.resetModules();
    await import("helper/axios");
  });

  it("refreshes a failed request only once", async () => {
    localStorage.setItem("refresh_token", JSON.stringify("refresh-token"));
    axiosMock.instance.get.mockResolvedValue({ payload: { token: "new-token", refresh_token: "new-refresh" } });
    const rejectResponse = axiosMock.responseErrorHandlers.at(-1)!;
    const request: Record<string, unknown> = { url: "/farm/list-farm" };

    await rejectResponse({ config: request, response: { status: 401 } });

    expect(request).toMatchObject({ _retry: true });
    expect(axiosMock.instance.get).toHaveBeenCalledTimes(1);
    expect(axiosMock.instance).toHaveBeenCalledWith(request);

    await expect(rejectResponse({ config: request, response: { status: 401 } })).rejects.toMatchObject({ response: { status: 401 } });
    expect(axiosMock.instance.get).toHaveBeenCalledTimes(1);
  });
});
