import { useMutation } from "@tanstack/react-query";
import { axios } from "helper/axios";

export const useSaveFeedingRation = () =>
  useMutation({
    mutationFn: ({
      cycle_id,
      ration_id,
      date,
      ration_number,
      feed_given,
      feed_leftover,
    }: {
      cycle_id: string;
      ration_id?: string;
      date: string;
      ration_number: string;
      feed_given: string;
      feed_leftover?: string;
    }) => {
      const payload = { ration_number, feed_given, feed_leftover, date };
      if (ration_id) {
        return axios
          .put(`/feeding/edit-feeding?cycle_id=${cycle_id}&ration_id=${ration_id}`, payload)
          .then((r: any) => r.payload);
      }
      return axios
        .post(`/feeding/add-feeding?cycle_id=${cycle_id}`, payload)
        .then((r: any) => r.payload);
    },
  });
