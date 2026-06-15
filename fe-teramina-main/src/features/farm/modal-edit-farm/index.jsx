import { Fragment } from "react";
import { Button, Dialog, DialogContent } from "@mui/material";
import { useToastStore } from "store/toast.store";
import NewFarm from "features/farm/new-farm";
import { useNewFarmForm } from "features/farm/new-farm/hooks";
import { useEditFarm } from "features/farm/queries";
import { useModal } from "hooks/useModal";
import { useTranslation } from "react-i18next";

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

const FarmEdit = ({ data, onClose }) => {
  const { t } = useTranslation();
  const { setToast: toast } = useToastStore();
  const { mutateAsync } = useEditFarm();

  const handleSubmit = async (value) => {
    try {
      const wizardFarmRegionState = {
        provinsi: JSON.parse(value.provinsi),
        kabupaten: JSON.parse(value.kabupaten),
        kecamatan: JSON.parse(value.kecamatan),
        kelurahan: JSON.parse(value.kelurahan),
      };

      await mutateAsync({
        farm_id: data._id,
        name: value.name,
        location: `${wizardFarmRegionState.kelurahan.name}, ${wizardFarmRegionState.kecamatan.name}, ${wizardFarmRegionState.kabupaten.name}, ${wizardFarmRegionState.provinsi.name}`,
      });

      await onClose();
      toast({ open: true, variant: "success", text: t("EDIT_DATA_SUCCESS_MESSAGE") });
    } catch {
      toast({ open: true, variant: "error", text: t("EDIT_DATA_FAILED_MESSAGE") });
    }
  };

  const form = useNewFarmForm({
    onSubmit: handleSubmit,
    defaultValues: { name: data.name, provinsi: "", kabupaten: "", kecamatan: "", kelurahan: "" },
  });

  return (
    <NewFarm
      formTitle="EDIT_FARM_DATA"
      actionText="SAVE"
      form={form}
      isModalComponent
    />
  );
};

const ModalFarmEdit = (props) => {
  const { t } = useTranslation();
  const { open, onOpen, onClose } = useModal();
  return (
    <Fragment>
      <Button aria-label={t("EDIT_FARM_DATA")} onClick={onOpen} sx={{ color: "#161616", minWidth: "unset !important", background: "rgba(71, 77, 164, 0.32)", marginRight: "5px", borderRadius: "6px", padding: "10.5px", "&:hover": { color: "#161616", background: "rgba(71, 77, 164, 0.6)" }, "& svg": { width: "20px", height: "20px" } }}>{ButtonLabel}</Button>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
        <DialogContent sx={{ padding: "0px !important" }}>
          <FarmEdit {...props} onClose={onClose} />
        </DialogContent>
      </Dialog>
    </Fragment>
  );
};

export default ModalFarmEdit;
