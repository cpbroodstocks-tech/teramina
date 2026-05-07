import { Fragment } from "react";
import { Button, Dialog, DialogContent } from "@mui/material";
import { useToastStore } from "store/toast.store";
import { useEditPond } from "features/pond/queries";
import NewPond from "features/farm/new-pond";
import { useNewPondForm } from "features/farm/new-pond/hooks";
import { constructionList, shapeList } from "features/farm/new-pond/define";
import { useModal } from "hooks/useModal";
import { useTranslation } from "react-i18next";

const convertLabelToValue = (label) => {
  const value = label.includes(" ") ? label.split(" ").join("") : label;
  return value.toLowerCase();
};

const isOtherConstructionLabel = (label) => {
  const filtered = constructionList.filter(
    (construction) => construction.value === convertLabelToValue(label)
  );
  return filtered.length > 0 ? false : true;
};

const isOtherShapeLabel = (label) => {
  const filtered = shapeList.filter(
    (construction) => construction.value === convertLabelToValue(label)
  );
  return filtered.length > 0 ? false : true;
};

const ButtonLabel = (
  <svg
    width="26"
    height="26"
    viewBox="0 0 26 26"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M15.3296 24.7295H25.0001"
      stroke="#161616"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M14.0488 2.07002C15.1664 0.646053 16.9725 0.720383 18.398 1.83802L20.5059 3.49097C21.9314 4.60861 22.4364 6.34191 21.3187 7.7689L8.7487 23.8056C8.32864 24.3424 7.68718 24.6594 7.00477 24.6669L2.15663 24.7291L1.05871 20.0053C0.904029 19.3426 1.05872 18.6451 1.47878 18.1067L14.0488 2.07002Z"
      stroke="#161616"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M11.6982 5.07227L18.9682 10.7712"
      stroke="#161616"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const PondEdit = ({ data, onClose }) => {
  const { t } = useTranslation();
  const { setToast: toast } = useToastStore();
  const { mutateAsync } = useEditPond();

  const handleSubmit = async (value) => {
    try {
      await mutateAsync({
        pond_id: data._id,
        name: value.name,
        size: value.size,
        pond_construction: value.construction.value === "other" ? value.otherConstructionLabel : value.construction.label,
        pond_shape: value.shape.value === "other" ? value.otherShapeLabel : value.shape.label,
        is_active: data.is_active,
      });
      await onClose();
      toast({ open: true, variant: "success", text: t("EDIT_DATA_SUCCESS_MESSAGE") });
    } catch {
      toast({ open: true, variant: "error", text: t("EDIT_DATA_FAILED_MESSAGE") });
    }
  };

  const formik = useNewPondForm({
    onSubmit: handleSubmit,
    defaultValues: {
      name: data.name,
      size: data.size,
      construction: {
        label: isOtherConstructionLabel(data.pond_construction) ? "Other" : data.pond_construction,
        value: isOtherConstructionLabel(data.pond_construction) ? "other" : convertLabelToValue(data.pond_construction),
      },
      otherConstructionLabel: isOtherConstructionLabel(data.pond_construction) ? data.pond_construction : "",
      shape: {
        label: isOtherShapeLabel(data.pond_shape) ? "Other" : data.pond_shape,
        value: isOtherShapeLabel(data.pond_shape) ? "other" : convertLabelToValue(data.pond_shape),
      },
      otherShapeLabel: isOtherShapeLabel(data.pond_shape) ? data.pond_shape : "",
    },
  });

  return (
    <NewPond
      formTitle="EDIT_POND_DATA"
      actionText="SAVE"
      formik={formik}
      isModalComponent
    />
  );
};

const ModalPondEdit = (props) => {
  const { open, onOpen, onClose } = useModal();
  return (
    <Fragment>
      <Button onClick={onOpen} sx={{ color: "#161616", minWidth: "unset !important", background: "rgba(71, 77, 164, 0.32)", marginRight: "5px", borderRadius: "6px", padding: "10.5px", "&:hover": { color: "#161616", background: "rgba(71, 77, 164, 0.6)" }, "& svg": { width: "20px", height: "20px" } }}>{ButtonLabel}</Button>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
        <DialogContent sx={{ padding: "0px !important" }}>
          <PondEdit {...props} onClose={onClose} />
        </DialogContent>
      </Dialog>
    </Fragment>
  );
};

export default ModalPondEdit;
