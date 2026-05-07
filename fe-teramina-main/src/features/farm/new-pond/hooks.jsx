import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslation } from "react-i18next";
import { z } from "zod";

const useNewPondForm = ({ onSubmit, defaultValues = undefined }) => {
  const { t } = useTranslation();
  const schema = z
    .object({
      name: z.string().min(1, t("FIELD_REQUIRED_MESSAGE")),
      size: z.coerce.number().min(0.001, "Value must be greater than 0."),
      construction: z.object({
        label: z.string().min(1),
        value: z.string().min(1),
      }),
      otherConstructionLabel: z.string().optional(),
      shape: z.object({
        label: z.string().min(1),
        value: z.string().min(1),
      }),
      otherShapeLabel: z.string().optional(),
    })
    .superRefine((data, ctx) => {
      if (data.construction.value === "other" && !data.otherConstructionLabel) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("FIELD_REQUIRED_MESSAGE"),
          path: ["otherConstructionLabel"],
        });
      }
      if (data.shape.value === "other" && !data.otherShapeLabel) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("FIELD_REQUIRED_MESSAGE"),
          path: ["otherShapeLabel"],
        });
      }
    });

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: defaultValues ?? {
      name: "",
      size: "",
      construction: { label: "HDPE", value: "hdpe" },
      otherConstructionLabel: "",
      shape: { label: "Persegi", value: "persegi" },
      otherShapeLabel: "",
    },
  });

  return {
    ...form,
    handleSubmit: form.handleSubmit(async (values) => {
      await onSubmit({
        name: values.name,
        size: values.size,
        construction: { ...values.construction },
        otherConstructionLabel: values.otherConstructionLabel,
        shape: { ...values.shape },
        otherShapeLabel: values.otherShapeLabel,
      });
    }),
  };
};

export { useNewPondForm };
