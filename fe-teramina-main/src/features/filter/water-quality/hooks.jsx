import dayjs from "dayjs";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { axios } from "helper/axios";
import { useEffect, useRef, useState } from "react";
import { useNDayAfter } from "hooks/useNDayAfter";
import { useToastStore } from "store/toast.store";
import { useFormatToQueryParams as formatToQueryParams } from "hooks/useFormatToQueryParams";
import { useTranslation } from "react-i18next";

const DOC_LENGTH = 120;

const FILTER_SCHEMA = z.object({
  farm_id: z.string().min(1),
  pond_id: z.string().min(1),
  cycle_id: z.array(z.string()).min(1),
  variables: z.array(z.string()).min(1),
  start_date: z.string().min(1),
  end_date: z.string().min(1),
});

const useFilter = (api) => {
  const { t } = useTranslation();
  const { setToast: toast } = useToastStore();
  const N_DOC_AFTER = useNDayAfter(new Date(), DOC_LENGTH);
  const filterQueryParams = useRef({
    farm_id: "",
    pond_id: "",
    cycle_id: [],
    variables: [],
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
    data: {},
    error: false,
  }));

  const { control, handleSubmit, reset, setValue, formState } = useForm({
    resolver: zodResolver(FILTER_SCHEMA),
    defaultValues: { farm_id: "", pond_id: "", cycle_id: [], variables: [], start_date: "", end_date: "" },
  });
  const formValues = useWatch({ control });

  const fetchMVPWithFilter = async (values) => {
    setFilter((previousValue) => ({
      ...previousValue,
      loading: true,
    }));

    const body = {
      cycles: values.cycle_id.join(","),
      start_date: dayjs(values.start_date).format("YYYY-MM-DD"),
      end_date: dayjs(values.end_date).format("YYYY-MM-DD"),
      variables: values.variables.join(","),
    };

    try {
      const response = await axios.get(
        `${api}?${new URLSearchParams(body).toString()}`
      );

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

  const formik = {
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
        cycle_id: [""],
      };
    },
    dirty: formState.isDirty,
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

    /**
     * SET THE TARGET FORMIK FIELD VALUE
     * BUT NOT FOR FILTER QUERY PARAMS DATE REF
     */

    if (key !== "start_date" || key !== "end_date")
      filterQueryParams.current[key] = value;
    setValue(key, value, { shouldDirty: true });

    /**
     * SET THE AFTER TARGET FORMIK FIELD VALUE TO EMPTY STRING
     * BUT NOT FOR FILTER QUERY PARAMS DATE REF
     */
    for (const field of fields.slice(indexToExclude + 1)) {
      if (field !== "start_date" || field !== "end_date")
        filterQueryParams.current[field] = "";
      if (field === "start_date" || field === "end_date")
        setValue(field, "");
      if (field === "cycle_id" || field === "variables")
        setValue(field, []);
      else {
        setValue(field, "");
      }
    }

    if (value === "") {
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
          resetFilterField[field] = [""];
          setValue("cycle_id", []);
        } else if (field === "variables") {
          resetFilterField[field] = [""];
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

    const response = await axios.get(url);
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
      updateListItem["daterange"] = {
        start_date: response.payload[0].data.start_date,
        end_date: response.payload[0].data.end_date,
      };
      updateListItem["variables"] = response.payload[0].data.variables;
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
        const filter = await axios.get("/dashboard/wq-filter");

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
    formik,
    onFilterChange: handleFilterChange,
  };
};

export { useFilter };
