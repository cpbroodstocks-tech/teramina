import Loader from "components/loader";
import PondList from "features/pond/pond-list";
import Error from "components/error";
import { usePondList } from "features/pond/queries";

const PondContent = () => {
  const { data, isLoading, isError } = usePondList();

  if (isLoading) return <Loader />;
  if (isError) return <Error />;
  return <PondList data={data} />;
};

export default PondContent;
