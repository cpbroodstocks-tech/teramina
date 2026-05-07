import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useNewFarmForm } from "features/farm/new-farm/hooks";

// i18next returns the key as-is in tests — no provider needed for error messages
describe("useNewFarmForm", () => {
  const validValues = {
    name: "My Farm",
    provinsi: "{\"id\":\"11\",\"name\":\"Aceh\"}",
    kabupaten: "{\"id\":\"1101\",\"name\":\"Simeulue\"}",
    kecamatan: "{\"id\":\"1101010\",\"name\":\"Teupah Selatan\"}",
    kelurahan: "{\"id\":\"1101010001\",\"name\":\"Latiung\"}",
  };

  it("initializes with empty default values", () => {
    const { result } = renderHook(() =>
      useNewFarmForm({ onSubmit: vi.fn() })
    );
    expect(result.current.getValues("name")).toBe("");
    expect(result.current.getValues("provinsi")).toBe("");
  });

  it("initializes with provided defaultValues", () => {
    const { result } = renderHook(() =>
      useNewFarmForm({
        onSubmit: vi.fn(),
        defaultValues: { ...validValues },
      })
    );
    expect(result.current.getValues("name")).toBe("My Farm");
    expect(result.current.getValues("provinsi")).toBe(validValues.provinsi);
  });

  it("calls onSubmit with form values when valid", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useNewFarmForm({ onSubmit, defaultValues: { ...validValues } })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmit).toHaveBeenCalledWith(validValues);
  });

  it("does not call onSubmit when name is empty", async () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() =>
      useNewFarmForm({
        onSubmit,
        defaultValues: { ...validValues, name: "" },
      })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("does not call onSubmit when a region field is empty", async () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() =>
      useNewFarmForm({
        onSubmit,
        defaultValues: { ...validValues, kabupaten: "" },
      })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });
});
