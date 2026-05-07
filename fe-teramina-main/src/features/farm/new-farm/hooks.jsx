import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslation } from "react-i18next";
import { z } from "zod";

const useNewFarmForm = ({ onSubmit, defaultValues = undefined }) => {
  const { t } = useTranslation();
  const schema = z.object({
    name: z.string().min(1, t("FIELD_REQUIRED_MESSAGE")),
    provinsi: z.string().min(1, t("FIELD_REQUIRED_MESSAGE")),
    kabupaten: z.string().min(1, t("FIELD_REQUIRED_MESSAGE")),
    kecamatan: z.string().min(1, t("FIELD_REQUIRED_MESSAGE")),
    kelurahan: z.string().min(1, t("FIELD_REQUIRED_MESSAGE")),
  });

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: defaultValues ?? {
      name: "",
      provinsi: "",
      kabupaten: "",
      kecamatan: "",
      kelurahan: "",
    },
  });

  return {
    ...form,
    handleSubmit: form.handleSubmit(async (values) => {
      await onSubmit(values);
    }),
  };
};

export { useNewFarmForm };
