import dayjs from "dayjs";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useEffect, useRef, useState } from "react";
import { useNDayAfter } from "hooks/useNDayAfter";
import { useToastStore } from "store/toast.store";
import { useTranslation } from "react-i18next";
import { fetchFilteredData, fetchFilterUrl } from "features/filter/queries";
import { loadSharedFilterContext, persistDashboardSelection } from "features/filter/shared-context";

const DOC_LENGTH = 120;

const FILTER_SCHEMA = z.object({
  farm_id: z.string().min(1),
  pond_id: z.string(),
  cycle_id: z.string(),
  date: z.string(),
});

const useFilter = (api) => {
  const { t } = useTranslation();
  const N_DOC_AFTER = useNDayAfter(new Date(), DOC_LENGTH);
  const filterQueryParams = useRef({
    farm_id: "",
    pond_id: "",
    cycle_id: "",
    filter_type: "historical",
  });

  const [filterList, setFilter] = useState(() => ({
    loading: true,
    filter: {
      farms: undefined,
      ponds: undefined,
      cycles: undefined,
      daterange: {
        start_date: dayjs(new Date()).format("MM/DD/YYYY"),
        end_date: dayjs(N_DOC_AFTER).format("MM/DD/YYYY"),
      },
    },
    data: {},
    error: false,
  }));

  const { control, handleSubmit, reset, setValue, formState } = useForm({
    resolver: zodResolver(FILTER_SCHEMA),
    defaultValues: { farm_id: "", pond_id: "", cycle_id: "", date: "" },
  });
  const formValues = useWatch({ control });

  const { setToast: toast } = useToastStore();

  const fetchMVPWithFilter = async (values) => {
    setFilter((previousValue) => ({
      ...previousValue,
      loading: true,
    }));

    try {
      const response = await fetchFilteredData(api, values);

      if (!response) throw response;

      setFilter((previousValue) => ({
        ...previousValue,
        data: response.payload,
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
          daterange: {
            start_date: dayjs(new Date()).format("MM/DD/YYYY"),
            end_date: dayjs(N_DOC_AFTER).format("MM/DD/YYYY"),
          },
        },
        data: {},
        error: false,
      }));

      filterQueryParams.current = {
        farm_id: "",
        pond_id: "",
        cycle_id: "",
        filter_type: "historical",
      };
    },
    dirty: formState.isDirty,
    setFieldValue: setValue,
  };

  const handleFilterChange = async (key, value) => {
    const fields = ["farm_id", "pond_id", "cycle_id", "date"];

    const indexToExclude = fields.indexOf(key);

    /**
     * SET THE TARGET FORMIK FIELD VALUE
     * BUT NOT FOR FILTER QUERY PARAMS DATE REF
     */
    if (key !== "date") filterQueryParams.current[key] = value;
    if (key !== "date") persistDashboardSelection(key, value, filterList.filter);
    setValue(key, value, { shouldDirty: true });

    /**
     * SET THE AFTER TARGET FORMIK FIELD VALUE TO EMPTY STRING
     * BUT NOT FOR FILTER QUERY PARAMS DATE REF
     */
    for (const field of fields.slice(indexToExclude + 1)) {
      if (field !== "date") filterQueryParams.current[field] = "";
      if (field === "date") setValue(field, "");
      else {
        setValue(field, "");
      }
    }

    if (value === "") {
      let fieldToReset = [];
      switch (key) {
      case "farm_id":
        fieldToReset = ["ponds", "cycles", "daterange"];
        break;
      case "pond_id":
        fieldToReset = ["cycles", "daterange"];
        break;
      case "cycle_id":
        fieldToReset = ["daterange"];
        break;
      default:
        fieldToReset = [];
        break;
      }

      let resetFilterField = {};
      for (const field of fieldToReset) {
        if (field === "daterange") {
          resetFilterField["daterange"] = {
            start_date: dayjs(new Date()).format("MM/DD/YYYY"),
            end_date: dayjs(N_DOC_AFTER).format("MM/DD/YYYY"),
          };
          setValue("date", "");
        } else {
          resetFilterField[field] = [];
        }
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
    case "cycle_id":
      updateListItem["daterange"] = response.payload[0].daterange;
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

  useEffect(() => {
    const fetchfilterListItem = async () => {
      try {
        const shared = await loadSharedFilterContext({ filterType: "historical" });
        if (!shared.values) throw shared;
        filterQueryParams.current = { ...shared.values, filter_type: "historical" };
        setValue("farm_id", shared.values.farm_id);
        setValue("pond_id", shared.values.pond_id);
        setValue("cycle_id", shared.values.cycle_id);
        setValue("date", shared.filter.daterange?.end_date || "");

        setFilter((previousValue) => ({
          ...previousValue,
          filter: {
            ...previousValue.filter,
            ...shared.filter,
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
  };
};

export { useFilter };
