import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  HARVEST_LENGTH,
  HARVEST_FORMAT,
  useGenerateHarvestSimulationFormValidationSchema,
} from "widgets/harvest/hooks";

const useAddHarverstSimulationPlanForm = ({ initialValues, onSubmit }) => {
  const schema = useGenerateHarvestSimulationFormValidationSchema(
    HARVEST_LENGTH,
    HARVEST_FORMAT,
    initialValues
  );

  const { handleSubmit, register, watch, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: initialValues,
  });

  return {
    handleSubmit: handleSubmit(onSubmit),
    register,
    watch,
    errors,
    isSubmitting,
    initialValues,
  };
};

export { useAddHarverstSimulationPlanForm };
