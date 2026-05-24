import dayjs from "dayjs";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useEffect, useRef, useState } from "react";
import { useNDayAfter } from "hooks/useNDayAfter";
import { fetchDashboardFilter, fetchFilterUrl } from "features/filter/queries";

const DOC_LENGTH = 120;

const FILTER_SCHEMA = z.object({
  farm_id: z.string().min(1),
  pond_id: z.string().min(1),
  cycle_id: z.string().min(1),
  date: z.string().min(1),
});

const useFilter = () => {
  const N_DOC_AFTER = useNDayAfter(new Date(), DOC_LENGTH);
  const filterQueryParams = useRef({
    farm_id: "",
    pond_id: "",
    cycle_id: "",
    filter_type: "historical",
  });

  const [selectedFilter, setSelectedFilter] = useState(() => ({
    date: "",
    cycle_id: "",
  }));

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
  }));

  const [submittedParams, setSubmittedParams] = useState(null);

  const { control, handleSubmit, reset, setValue, formState } = useForm({
    resolver: zodResolver(FILTER_SCHEMA),
    defaultValues: { farm_id: "", pond_id: "", cycle_id: "", date: "" },
  });
  const formValues = useWatch({ control });

  const form = {
    values: formValues,
    handleSubmit: handleSubmit((values) => {
      setSelectedFilter({ date: values.date, cycle_id: values.cycle_id });
      setSubmittedParams({
        ...filterQueryParams.current,
        date: values.date,
      });
    }),
    handleReset: () => {
      reset();
      setSubmittedParams(null);
      setSelectedFilter({ date: "", cycle_id: "" });
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

    if (key !== "date") filterQueryParams.current[key] = value;
    setValue(key, value, { shouldDirty: true });

    for (const field of fields.slice(indexToExclude + 1)) {
      if (field !== "date") filterQueryParams.current[field] = "";
      if (field === "date") setValue(field, "");
      else setValue(field, "");
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
        const filter = await fetchDashboardFilter();
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
    selectedFilter,
    submittedParams,
  };
};

export { useFilter };
