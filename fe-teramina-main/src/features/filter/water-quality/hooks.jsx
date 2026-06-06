import dayjs from "dayjs";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useEffect, useRef, useState } from "react";
import { useNDayAfter } from "hooks/useNDayAfter";
import { useFormatToQueryParams as formatToQueryParams } from "hooks/useFormatToQueryParams";
import { fetchFilterUrl, fetchWaterQualityFilter } from "features/filter/queries";

const DOC_LENGTH = 120;

const FILTER_SCHEMA = z.object({
  farm_id: z.string().min(1),
  pond_id: z.string().min(1),
  cycle_id: z.array(z.string()).min(1),
  variables: z.array(z.string()).min(1),
  start_date: z.string().min(1),
  end_date: z.string().min(1),
});

const useFilter = () => {
  const N_DOC_AFTER = useNDayAfter(new Date(), DOC_LENGTH);
  const filterQueryParams = useRef({
    farm_id: "",
    pond_id: "",
    cycle_id: [],
  });

  const [filterList, setFilter] = useState(() => ({
    loading: true,
    filter: {
      farms: undefined,
      ponds: undefined,
      cycles: [],
      daterange: {
        start_date: dayjs(new Date()).format("MM/DD/YYYY"),
        end_date: dayjs(N_DOC_AFTER).format("MM/DD/YYYY"),
      },
      variables: [],
    },
  }));

  const [submittedParams, setSubmittedParams] = useState(null);

  const { control, handleSubmit, reset, setValue, formState } = useForm({
    resolver: zodResolver(FILTER_SCHEMA),
    defaultValues: { farm_id: "", pond_id: "", cycle_id: [], variables: [], start_date: "", end_date: "" },
  });
  const formValues = useWatch({ control });

  const form = {
    values: formValues,
    handleSubmit: handleSubmit((values) => {
      setSubmittedParams({
        cycles: values.cycle_id.join(","),
        start_date: dayjs(values.start_date).format("YYYY-MM-DD"),
        end_date: dayjs(values.end_date).format("YYYY-MM-DD"),
        variables: values.variables.join(","),
      });
    }),
    handleReset: () => {
      reset();
      setSubmittedParams(null);
      setFilter((previousValue) => ({
        ...previousValue,
        filter: {
          farms: previousValue.filter.farms,
          ponds: undefined,
          cycles: [],
          daterange: {
            start_date: dayjs(new Date()).format("MM/DD/YYYY"),
            end_date: dayjs(N_DOC_AFTER).format("MM/DD/YYYY"),
          },
          variables: [],
        },
      }));
      filterQueryParams.current = {
        farm_id: "",
        pond_id: "",
        cycle_id: [],
      };
    },
    dirty: formState.isDirty,
    errors: formState.errors,
    setFieldValue: setValue,
  };

  const handleFilterChange = async (key, value) => {
    const fields = [
      "farm_id",
      "pond_id",
      "cycle_id",
      "start_date",
      "end_date",
      "variables",
    ];

    const indexToExclude = fields.indexOf(key);

    if (["farm_id", "pond_id", "cycle_id"].includes(key))
      filterQueryParams.current[key] = value;
    setValue(key, value, { shouldDirty: true });

    for (const field of fields.slice(indexToExclude + 1)) {
      if (["farm_id", "pond_id", "cycle_id"].includes(field))
        filterQueryParams.current[field] = field === "cycle_id" ? [] : "";
      if (field === "start_date" || field === "end_date")
        setValue(field, "");
      if (field === "cycle_id" || field === "variables")
        setValue(field, []);
      else {
        setValue(field, "");
      }
    }

    if (value === "" || (Array.isArray(value) && value.length === 0)) {
      let fieldToReset = [];
      switch (key) {
      case "farm_id":
        fieldToReset = ["ponds", "cycles", "daterange", "variables"];
        break;
      case "pond_id":
        fieldToReset = ["cycles", "daterange", "variables"];
        break;
      case "cycle_id":
        fieldToReset = ["daterange", "variables"];
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
          setValue("start_date", "");
          setValue("end_date", "");
        } else if (field === "cycles") {
          resetFilterField[field] = [];
          setValue("cycle_id", []);
        } else if (field === "variables") {
          resetFilterField[field] = [];
          setValue("variables", []);
        } else {
          resetFilterField[field] = "";
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

    let url = "/dashboard/wq-filter";
    url = `${url}?${formatToQueryParams(filterQueryParams.current)}`;

    let response;
    try {
      response = await fetchFilterUrl(url);
    } catch {
      return;
    }

    const payload = Array.isArray(response?.payload) ? response.payload : [];

    const updateListItem = {};
    switch (key) {
    case "farm_id":
      updateListItem["ponds"] = payload;
      break;
    case "pond_id":
      updateListItem["cycles"] = payload;
      break;
    case "cycle_id": {
      const cycleMetadata = payload[0]?.data;
      if (!cycleMetadata) return;
      updateListItem["daterange"] = {
        start_date: cycleMetadata.start_date,
        end_date: cycleMetadata.end_date,
      };
      updateListItem["variables"] = Array.isArray(cycleMetadata.variables) ? cycleMetadata.variables : [];
      break;
    }
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
        const filter = await fetchWaterQualityFilter();
        if (!filter) throw filter;
        setFilter((previousValue) => ({
          ...previousValue,
          filter: {
            ...previousValue.filter,
            farms: filter.payload,
          },
        }));
      } catch {
        // filter list unavailable — farms remains undefined
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
    submittedParams,
  };
};

export { useFilter };
