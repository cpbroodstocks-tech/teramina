import { describe, it, expect } from "vitest";
import { z } from "zod";

const pondSchema = z
  .object({
    name: z.string().min(1, "FIELD_REQUIRED_MESSAGE"),
    size: z.coerce.number().min(0.001, "Value must be greater than 0."),
    construction: z.object({ label: z.string().min(1), value: z.string().min(1) }),
    otherConstructionLabel: z.string().optional(),
    shape: z.object({ label: z.string().min(1), value: z.string().min(1) }),
    otherShapeLabel: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.construction.value === "other" && !data.otherConstructionLabel) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "FIELD_REQUIRED_MESSAGE", path: ["otherConstructionLabel"] });
    }
    if (data.shape.value === "other" && !data.otherShapeLabel) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "FIELD_REQUIRED_MESSAGE", path: ["otherShapeLabel"] });
    }
  });

const validPond = {
  name: "Pond A",
  size: 100,
  construction: { label: "HDPE", value: "hdpe" },
  otherConstructionLabel: "",
  shape: { label: "Persegi", value: "persegi" },
  otherShapeLabel: "",
};

describe("pond schema", () => {
  it("passes with valid values", () => {
    expect(pondSchema.safeParse(validPond).success).toBe(true);
  });

  it("fails when name is empty", () => {
    expect(pondSchema.safeParse({ ...validPond, name: "" }).success).toBe(false);
  });

  it("fails when size is zero", () => {
    expect(pondSchema.safeParse({ ...validPond, size: 0 }).success).toBe(false);
  });

  it("requires otherConstructionLabel when construction is other", () => {
    const result = pondSchema.safeParse({
      ...validPond,
      construction: { label: "Other", value: "other" },
      otherConstructionLabel: "",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const paths = result.error.issues.map((i) => i.path[0]);
      expect(paths).toContain("otherConstructionLabel");
    }
  });

  it("passes when construction is other with a label", () => {
    const result = pondSchema.safeParse({
      ...validPond,
      construction: { label: "Other", value: "other" },
      otherConstructionLabel: "Beton",
    });
    expect(result.success).toBe(true);
  });
});
