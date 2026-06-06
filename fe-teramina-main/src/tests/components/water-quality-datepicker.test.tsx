import dayjs from "dayjs";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { StartDatePickerPopUp } from "features/filter/water-quality/components/datepicker-popup";

vi.mock("@mui/x-date-pickers/StaticDatePicker", () => ({
  StaticDatePicker: ({ onChange }: { onChange: (value: dayjs.Dayjs) => void }) => (
    <button type="button" onClick={() => onChange(dayjs("2024-05-01"))}>
      Pick date
    </button>
  ),
}));

vi.mock("features/filter/default/components/datepicker-popup/styles", () => ({
  useStyles: () => ({ classes: {} }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

describe("Water Quality date picker", () => {
  it("restores focus to the trigger before closing", async () => {
    const setFieldValue = vi.fn();
    render(
      <StartDatePickerPopUp
        form={{ values: { start_date: "" }, setFieldValue }}
        daterange={{ start_date: "03/01/2024", end_date: "06/28/2024" }}
      />
    );

    const trigger = screen.getByRole("button", { name: "START_DATE" });
    await userEvent.click(trigger);
    await userEvent.click(screen.getByRole("button", { name: "Pick date" }));

    expect(setFieldValue).toHaveBeenCalledWith("start_date", "05/01/2024");
    expect(trigger).toHaveFocus();
  });
});
