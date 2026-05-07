import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useNewPondForm } from "features/farm/new-pond/hooks";

describe("useNewPondForm", () => {
  const validValues = {
    name: "Pond A",
    size: 100,
    construction: { label: "HDPE", value: "hdpe" },
    otherConstructionLabel: "",
    shape: { label: "Persegi", value: "persegi" },
    otherShapeLabel: "",
  };

  it("initializes with empty default values", () => {
    const { result } = renderHook(() => useNewPondForm({ onSubmit: vi.fn() }));
    expect(result.current.getValues("name")).toBe("");
  });

  it("calls onSubmit with valid values", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useNewPondForm({ onSubmit, defaultValues: validValues })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmit).toHaveBeenCalledWith(validValues);
  });

  it("does not call onSubmit when name is empty", async () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() =>
      useNewPondForm({ onSubmit, defaultValues: { ...validValues, name: "" } })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("does not call onSubmit when size is zero", async () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() =>
      useNewPondForm({ onSubmit, defaultValues: { ...validValues, size: 0 } })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("does not call onSubmit when construction is other with no label", async () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() =>
      useNewPondForm({
        onSubmit,
        defaultValues: {
          ...validValues,
          construction: { label: "Other", value: "other" },
          otherConstructionLabel: "",
        },
      })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });
});
