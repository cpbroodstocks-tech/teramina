import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import dayjs from "dayjs";
import { useNewCycleForm } from "features/farm/new-cycle/hooks";

describe("useNewCycleForm", () => {
  const validValues = { name: "Cycle 1", date: dayjs("2024-01-15") };

  it("initializes with empty name", () => {
    const { result } = renderHook(() => useNewCycleForm({ onSubmit: vi.fn() }));
    expect(result.current.getValues("name")).toBe("");
  });

  it("calls onSubmit with valid values", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useNewCycleForm({ onSubmit, defaultValues: validValues })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmit).toHaveBeenCalledWith({ name: validValues.name, date: validValues.date });
  });

  it("does not call onSubmit when name is empty", async () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() =>
      useNewCycleForm({ onSubmit, defaultValues: { ...validValues, name: "" } })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });
});
