import * as Yup from "yup";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import {
  HARVEST_LENGTH,
  HARVEST_FORMAT,
  useGenerateHarvestSimulationFormValidationSchema,
} from "widgets/harvest/hooks";

const useAddHarverstSimulationPlanForm = ({ initialValues, onSubmit }) => {
  const SCHEMA = useGenerateHarvestSimulationFormValidationSchema(
    HARVEST_LENGTH,
    HARVEST_FORMAT,
    initialValues
  );

  const { handleSubmit, register, watch, formState: { errors, isSubmitting } } = useForm({
    resolver: yupResolver(Yup.object().shape(SCHEMA)),
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
