import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useEffect, useRef, useState } from "react";
import { useToastStore } from "store/toast.store";
import { useTranslation } from "react-i18next";
import { fetchDashboardFilter, fetchFilteredData, fetchFilterUrl } from "features/filter/queries";

const FILTER_SCHEMA = z.object({
  farm_id: z.string().min(1),
  pond_id: z.string().min(1),
  cycle_id: z.string().min(1),
});

const useFilter = (api) => {
  const { t } = useTranslation();
  const { setToast: toast } = useToastStore();
  const filterQueryParams = useRef({
    farm_id: "",
    pond_id: "",
    cycle_id: "",
  });

  const [selectedFilter, setSelectedFilter] = useState(() => ({
    cycle_id: "",
  }));
  const [filterList, setFilter] = useState(() => ({
    loading: true,
    filter: {
      farms: undefined,
      ponds: undefined,
      cycles: undefined,
    },
    data: {},
    error: false,
  }));

  const { control, handleSubmit, reset, setValue, getValues, formState } = useForm({
    resolver: zodResolver(FILTER_SCHEMA),
    defaultValues: { farm_id: "", pond_id: "", cycle_id: "" },
  });
  const formValues = useWatch({ control });

  const fetchMVPWithFilter = async (values) => {
    setFilter((previousValue) => ({
      ...previousValue,
      loading: true,
    }));

    try {
      const response = await Promise.all(
        api.map((api) => fetchFilteredData(api, values))
      );
      if (!response) throw response;

      setFilter((previousValue) => ({
        ...previousValue,
        data: {
          harvestRecord: response[0].payload,
          harvestRecomendation: response[1].payload,
        },
        error: false,
      }));
    } catch (err) {
      const errorMessage =
        err.response?.data?.message || t("SOMETHING_WENT_WRONG");
      toast({
        open: true,
        variant: "error",
        text: errorMessage,
      });

      setFilter((previousValue) => ({
        ...previousValue,
        error: true,
      }));
    } finally {
      setFilter((previousValue) => ({
        ...previousValue,
        loading: false,
      }));
    }
  };

  const form = {
    values: formValues,
    handleSubmit: handleSubmit((values) => {
      setSelectedFilter({
        cycle_id: values.cycle_id,
      });
      fetchMVPWithFilter(values);
    }),
    handleReset: () => {
      reset();
      setFilter((previousValue) => ({
        ...previousValue,
        filter: {
          farms: previousValue.filter.farms,
          ponds: undefined,
          cycles: undefined,
        },
        data: {},
        error: false,
      }));

      filterQueryParams.current = {
        farm_id: "",
        pond_id: "",
        cycle_id: "",
      };
    },
    dirty: formState.isDirty,
    setFieldValue: setValue,
  };

  const handleFilterChange = async (key, value) => {
    const fields = ["farm_id", "pond_id", "cycle_id"];

    const indexToExclude = fields.indexOf(key);

    filterQueryParams.current[key] = value;
    setValue(key, value, { shouldDirty: true });

    /**
     * SET THE AFTER TARGET FORMIK FIELD VALUE TO EMPTY STRING
     * BUT NOT FOR FILTER QUERY PARAMS DATE REF
     */
    for (const field of fields.slice(indexToExclude + 1)) {
      filterQueryParams.current[field] = "";
      setValue(field, "");
    }

    if (value === "") {
      let fieldToReset = [];
      switch (key) {
      case "farm_id":
        fieldToReset = ["ponds", "cycles"];
        break;
      case "pond_id":
        fieldToReset = ["cycles"];
        break;
      case "cycle_id":
        fieldToReset = [];
        break;
      default:
        fieldToReset = [];
        break;
      }

      let resetFilterField = {};
      for (const field of fieldToReset) {
        resetFilterField[field] = [];
      }

      setFilter((previousValue) => ({
        ...previousValue,
        filter: {
          ...previousValue.filter,
          ...resetFilterField,
        },
      }));

      return;
    }

    let url = "/dashboard/filter";
    url = `${url}?${new URLSearchParams(filterQueryParams.current).toString()}`;

    const response = await fetchFilterUrl(url);
    if (!response) throw response;

    const updateListItem = {};
    switch (key) {
    case "farm_id":
      updateListItem["ponds"] = response.payload;
      break;
    case "pond_id":
      updateListItem["cycles"] = response.payload;
      break;
    }

    setFilter((previousValue) => ({
      ...previousValue,
      filter: {
        ...previousValue.filter,
        ...updateListItem,
      },
    }));
  };

  const refetch = () =>
    fetchMVPWithFilter({
      farm_id: getValues("farm_id"),
      pond_id: getValues("pond_id"),
      cycle_id: getValues("cycle_id"),
    });

  useEffect(() => {
    const fetchfilterListItem = async () => {
      try {
        const filter = await fetchDashboardFilter();

        if (!filter) throw filter;

        setFilter((previousValue) => ({
          ...previousValue,
          filter: {
            ...previousValue.filter,
            farms: filter.payload,
          },
          error: false,
        }));
      } catch (err) {
        setFilter((previousValue) => ({
          ...previousValue,
          error: true,
        }));
      } finally {
        setFilter((previousValue) => ({
          ...previousValue,
          loading: false,
        }));
      }
    };
    fetchfilterListItem();
  }, []);

  return {
    ...filterList,
    form,
    onFilterChange: handleFilterChange,
    selectedFilter: selectedFilter,
    refetch: refetch,
  };
};

export { useFilter };
