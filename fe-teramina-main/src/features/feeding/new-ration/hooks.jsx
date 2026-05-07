import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslation } from "react-i18next";
import { z } from "zod";

const useRationForm = ({ onSubmit, initialValues }) => {
  const { t } = useTranslation();
  const schema = z.object({
    ration_id: z.string().optional(),
    ration_number: z.string().min(1, t("FIELD_REQUIRED_MESSAGE")),
    feed_given: z.string().min(1, t("FIELD_REQUIRED_MESSAGE")),
    feed_leftover: z.union([z.string(), z.undefined()]).optional(),
  });

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      ration_id: initialValues.ration_id,
      ration_number: initialValues.ration_number,
      feed_given: initialValues.realized,
      feed_leftover: initialValues.leftover,
    },
  });

  return {
    ...form,
    handleSubmit: form.handleSubmit(async (values) => {
      await onSubmit(values);
    }),
  };
};

export { useRationForm };
