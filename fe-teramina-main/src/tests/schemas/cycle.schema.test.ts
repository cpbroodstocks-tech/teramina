import { describe, it, expect } from "vitest";
import { z } from "zod";
import dayjs from "dayjs";

const cycleSchema = z.object({
  name: z.string().min(1, "FIELD_REQUIRED_MESSAGE"),
  date: z.any(),
});

describe("cycle schema", () => {
  it("passes with valid values", () => {
    const result = cycleSchema.safeParse({ name: "Cycle 1", date: dayjs() });
    expect(result.success).toBe(true);
  });

  it("fails when name is empty", () => {
    const result = cycleSchema.safeParse({ name: "", date: dayjs() });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("FIELD_REQUIRED_MESSAGE");
    }
  });
});
