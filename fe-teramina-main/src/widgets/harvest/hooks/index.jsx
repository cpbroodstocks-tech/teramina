import * as Yup from "yup";

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

const useGenerateHarvestSimulationFormValidationSchema = (
  length,
  format,
  initialValues
) => {
  const schema = {};
  const lastDOC = initialValues.cycle_info.last_doc;

  for (const property in format) {
    if (property === "partial1") {
      schema[property] = Yup.object().shape({
        doc:
          initialValues[property].doc !== ""
            ? Yup.number().required()
            : Yup.number()
              .min(lastDOC + 1)
              .required(),
        biomass: Yup.number().required(),
      });
    }

    if (property === "final") {
      schema[property] = Yup.object({
        doc: Yup.number(),
        biomass: Yup.number(),
      }).when(
        [Object.keys(format)[length - 2]],
        (value, _, { originalValue }) => {
          const docBefore = parseInt(value.doc, 10);
          const docAfter = originalValue.doc
            ? parseInt(originalValue.doc, 10)
            : 0;

          if (initialValues[property].doc !== "") {
            return Yup.object().shape({
              doc:
                docBefore > docAfter
                  ? Yup.number()
                    .min(docBefore + 1)
                    .required()
                  : Yup.number().required(),
              biomass: Yup.number().required(),
            });
          }

          return Yup.object().shape({
            doc: Yup.number().test(
              "isPreferedValue",
              () => {
                const propName = property.replace(/\d+/, match => ` ${match}`);
                const lastDocPropName = Object.keys(format)[length - 2].replace(/\d+/, match => ` ${match}`);
                return `${propName} must be greater than ${lastDocPropName} and greater than last doc`;
              },
              (value) => value > lastDOC && value > docBefore
            ).required(),
            biomass: Yup.number().required(),
          });
        }
      );
    }

    if (property !== "final" && property !== "partial1") {
      const indexOfProperties = Object.keys(format).indexOf(property);

      schema[property] = Yup.object({
        doc: Yup.number().required(),
        biomass: Yup.number().required(),
      }).when(
        [Object.keys(format)[indexOfProperties - 1]],
        (value, _, { originalValue }) => {
          const docBefore = parseInt(value.doc, 10);
          const docAfter = originalValue.doc
            ? parseInt(originalValue.doc, 10)
            : 0;

          if (initialValues[property].doc !== "") {
            return Yup.object().shape({
              doc:
                docBefore > docAfter
                  ? Yup.number()
                    .min(docBefore + 1)
                    .required()
                  : Yup.number().required(),
              biomass: Yup.number().required(),
            });
          }

          return Yup.object().shape({
            doc: Yup.number().test(
              "isPreferedValue",
              () => {
                const propName = property.replace(/\d+/, match => ` ${match}`);
                const lastDocPropName = Object.keys(format)[indexOfProperties - 1].replace(/\d+/, match => ` ${match}`);
                return `${propName} must be greater than ${lastDocPropName} and greater than last doc`;
              },
              (value) => value > lastDOC && value > docBefore
            ).required(),
            biomass: Yup.number().required(),
          });
        }
      );
    }
  }
  return schema;
};

export {
  HARFEST_SCHEMA,
  HARVEST_FORMAT,
  HARVEST_LENGTH,
  generateBody,
  generateHarvestInitialValues,
  useGenerateHarvestSimulationFormValidationSchema,
};
