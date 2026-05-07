import { Fragment } from "react";
import Stepper from "features/farm/stepper";
import Loader from "components/loader";
import FarmList from "features/farm/farm-list";
import Error from "components/error";
import { useFarmList, useInvalidateFarmList } from "features/farm/queries";

const Farm = () => {
  const { data, isLoading, isError } = useFarmList();
  const refetch = useInvalidateFarmList();

  if (isLoading) return <Loader />;
  if (isError) return <Error />;
  if (data.length === 0) {
    return (
      <Fragment>
        <Stepper onDoneSubmit={refetch} />
      </Fragment>
    );
  }

  return <FarmList data={data} />;
};

export default Farm;
