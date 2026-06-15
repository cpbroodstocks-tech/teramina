import DatePickerPopUp from "features/filter/default/components/datepicker-popup";
import PageFilterBar from "components/page-filter-bar";

const Filter = ({ filter, form }) => (
  <form onSubmit={form.handleSubmit}>
    <PageFilterBar
      dirty={form.dirty}
      disabled={Object.keys(form.errors || {}).length > 0}
      onReset={form.handleReset}
    >
      <DatePickerPopUp form={form} daterange={filter.daterange} />
    </PageFilterBar>
  </form>
);

export default Filter;
