import { z } from "zod";

const HARVEST_LENGTH = 4;
const HARFEST_SCHEMA = {
  doc: "",
  biomass: "",
  revenue: "",
};
const HARVEST_FORMAT = Object.fromEntries(
  new Map(
    Array.from(Array(HARVEST_LENGTH), (_, key) => {
      if (key === HARVEST_LENGTH - 1) return ["final", HARFEST_SCHEMA];
      return [`partial${key + 1}`, HARFEST_SCHEMA];
    })
  )
);

const generateBody = (format, current, values) => {
  if (values.harvest_type === "partial") {
    if (current.length === 0) {
      format.partial1 = {
        doc: parseInt(values.harvest_doc, 10),
        biomass: parseInt(values.harvest_biomass, 10),
        revenue: parseInt(values.harvest_revenue, 10),
      };
    } else {
      const keys = Object.keys(format)
        .filter((v) => v !== "final")
        .sort((a, b) => a - b);

      for (var key of keys) {
        if (format[key].doc === "" && format[key].biomass === "") {
          format[key] = {
            doc: parseInt(values.harvest_doc, 10),
            biomass: parseInt(values.harvest_biomass, 10),
            revenue: parseInt(values.harvest_revenue, 10),
          };
          break;
        }
      }
    }
  }

  if (values.harvest_type === "final") {
    format.final = {
      doc: parseInt(values.harvest_doc, 10),
      biomass: parseInt(values.harvest_biomass, 10),
      revenue: parseInt(values.harvest_revenue, 10),
    };
  }

  return format;
};

const generateHarvestInitialValues = (current) => {
  const format = Object.assign({}, HARVEST_FORMAT);
  if (current.length === 0) return format;
  for (var value of current) {
    if (value.harvest_type === "partial") {
      format[`${value.harvest_type}${value.harvest_no}`] = {
        doc: value.doc,
        biomass: parseInt(value.biomass_kg.replace(/\D/g, ""), 10),
        revenue: parseInt(value.revenue.replace(/\D/g, ""), 10),
      };
    } else {
      format["final"] = {
        doc: value.doc,
        biomass: parseInt(value.biomass_kg.replace(/\D/g, ""), 10),
        revenue: parseInt(value.revenue.replace(/\D/g, ""), 10),
      };
    }
  }
  return format;
};

const formatHarvestPropertyName = (property) => property.replace(/\d+/, match => ` ${match}`);

const requiredNumber = () => z.preprocess(
  (value) => (value === "" || value === null || value === undefined ? undefined : Number(value)),
  z.number({ invalid_type_error: "Required", required_error: "Required" })
);

const harvestRowSchema = () => z.object({
  doc: requiredNumber(),
  biomass: requiredNumber(),
});

const useGenerateHarvestSimulationFormValidationSchema = (
  length,
  format,
  initialValues
) => {
  const schema = {};
  const lastDOC = initialValues.cycle_info.last_doc;

  for (const property in format) {
    if (property === "partial1") {
      schema[property] = harvestRowSchema().superRefine((value, ctx) => {
        if (initialValues[property].doc === "" && value.doc < lastDOC + 1) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `Number must be greater than or equal to ${lastDOC + 1}`,
            path: ["doc"],
          });
        }
      });
    }

    if (property === "final") {
      schema[property] = harvestRowSchema();
    }

    if (property !== "partial1") {
      schema[property] = harvestRowSchema();
    }
  }

  return z.object(schema).superRefine((values, ctx) => {
    for (const property in format) {
      if (property === "partial1") continue;

      const indexOfProperties = Object.keys(format).indexOf(property);
      const previousProperty = property === "final"
        ? Object.keys(format)[length - 2]
        : Object.keys(format)[indexOfProperties - 1];
      const docBefore = parseInt(values[previousProperty]?.doc, 10);
      const docAfter = values[property]?.doc ? parseInt(values[property].doc, 10) : 0;

      if (initialValues[property].doc !== "") {
        if (docBefore > docAfter && values[property].doc < docBefore + 1) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `Number must be greater than or equal to ${docBefore + 1}`,
            path: [property, "doc"],
          });
        }
        continue;
      }

      if (!(values[property].doc > lastDOC && values[property].doc > docBefore)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `${formatHarvestPropertyName(property)} must be greater than ${formatHarvestPropertyName(previousProperty)} and greater than last doc`,
          path: [property, "doc"],
        });
      }
    }
  });
};

export {
  HARFEST_SCHEMA,
  HARVEST_FORMAT,
  HARVEST_LENGTH,
  generateBody,
  generateHarvestInitialValues,
  useGenerateHarvestSimulationFormValidationSchema,
};
