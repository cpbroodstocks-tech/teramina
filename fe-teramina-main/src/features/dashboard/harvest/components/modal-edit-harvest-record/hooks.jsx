import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const useEditHarvestRecordForm = ({ initialValues, onSubmit }) => {
  const schema = z.object({
    harvest_type: z.string().min(1, "Tidak Boleh Kosong"),
    harvest_doc: z.coerce.number({ invalid_type_error: "Tidak Boleh Kosong" }),
    harvest_biomass: z.coerce.number({ invalid_type_error: "Tidak Boleh Kosong" }),
    harvest_revenue: z.coerce.number({ invalid_type_error: "Tidak Boleh Kosong" }),
  });

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      harvest_type: initialValues.harvest_type,
      harvest_doc: initialValues.doc,
      harvest_biomass: initialValues.biomass_kg.replace(/\D/g, ""),
      harvest_revenue: initialValues.revenue.replace(/\D/g, ""),
    },
  });

  return {
    ...form,
    handleSubmit: form.handleSubmit(async (values) => {
      await onSubmit(values);
    }),
  };
};

export { useEditHarvestRecordForm };
