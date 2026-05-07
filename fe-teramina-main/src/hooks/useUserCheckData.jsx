import { useQuery } from "@tanstack/react-query";
import { axios } from "helper/axios";

const useUserCheckData = () => {
  const { isLoading, isError, data } = useQuery({
    queryKey: ["user-data-status"],
    queryFn: () => axios.get("/user/user-data-status").then((r) => r?.payload?.is_there_data),
  });

  return { loading: isLoading, error: isError, data };
};

export { useUserCheckData };
