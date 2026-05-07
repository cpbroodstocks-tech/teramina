import { describe, it, expect } from "vitest";
import { z } from "zod";

const farmSchema = z.object({
  name: z.string().min(1, "FIELD_REQUIRED_MESSAGE"),
  provinsi: z.string().min(1, "FIELD_REQUIRED_MESSAGE"),
  kabupaten: z.string().min(1, "FIELD_REQUIRED_MESSAGE"),
  kecamatan: z.string().min(1, "FIELD_REQUIRED_MESSAGE"),
  kelurahan: z.string().min(1, "FIELD_REQUIRED_MESSAGE"),
});

describe("farm schema", () => {
  const validFarm = {
    name: "My Farm",
    provinsi: "{\"id\":\"11\",\"name\":\"Aceh\"}",
    kabupaten: "{\"id\":\"1101\",\"name\":\"Simeulue\"}",
    kecamatan: "{\"id\":\"1101010\",\"name\":\"Teupah Selatan\"}",
    kelurahan: "{\"id\":\"1101010001\",\"name\":\"Latiung\"}",
  };

  it("passes with all valid values", () => {
    const result = farmSchema.safeParse(validFarm);
    expect(result.success).toBe(true);
  });

  it("fails when name is empty", () => {
    const result = farmSchema.safeParse({ ...validFarm, name: "" });
    expect(result.success).toBe(false);
  });

  it("fails when provinsi is missing", () => {
    const result = farmSchema.safeParse({ ...validFarm, provinsi: "" });
    expect(result.success).toBe(false);
  });
});
