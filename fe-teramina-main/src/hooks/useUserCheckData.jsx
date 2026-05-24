import { useUserDataStatus } from "features/user/queries";

const useUserCheckData = () => {
  const { isLoading, isError, data } = useUserDataStatus();

  return { loading: isLoading, error: isError, data };
};

export { useUserCheckData };
