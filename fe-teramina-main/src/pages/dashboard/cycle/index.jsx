import Loader from "components/loader";
import CycleList from "features/cycle/cycle-list";
import Error from "components/error";
import { useCycleList } from "features/cycle/queries";

const CycleContent = () => {
  const { data, isLoading, isError } = useCycleList();

  if (isLoading) return <Loader />;
  if (isError) return <Error />;
  return <CycleList data={data} />;
};

export default CycleContent;
