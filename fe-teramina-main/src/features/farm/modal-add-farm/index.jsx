import { Fragment } from "react";
import { Button, Dialog, DialogContent } from "@mui/material";
import { useToastStore } from "store/toast.store";
import NewFarm from "features/farm/new-farm";
import { useNewFarmForm } from "features/farm/new-farm/hooks";
import { useAddFarm } from "features/farm/queries";
import { useModal } from "hooks/useModal";
import { useTranslation } from "react-i18next";

const FarmAdd = ({ onClose }) => {
  const { t } = useTranslation();
  const { setToast: toast } = useToastStore();
  const { mutateAsync } = useAddFarm();

  const handleSubmit = async (value) => {
    try {
      const wizardFarmRegionState = {
        provinsi: JSON.parse(value.provinsi),
        kabupaten: JSON.parse(value.kabupaten),
        kecamatan: JSON.parse(value.kecamatan),
        kelurahan: JSON.parse(value.kelurahan),
      };

      await mutateAsync({
        name: value.name,
        location: `${wizardFarmRegionState.kelurahan.name}, ${wizardFarmRegionState.kecamatan.name}, ${wizardFarmRegionState.kabupaten.name}, ${wizardFarmRegionState.provinsi.name}`,
      });

      await onClose();
      toast({ open: true, variant: "success", text: t("ADD_DATA_SUCCESS_MESSAGE") });
    } catch {
      toast({ open: true, variant: "error", text: t("ADD_DATA_FAILED_MESSAGE") });
    }
  };

  const formik = useNewFarmForm({ onSubmit: handleSubmit });
  return <NewFarm isModalComponent formik={formik} />;
};

const ModalFarmAdd = (props) => {
  const { t } = useTranslation();
  const { open, onOpen, onClose } = useModal();
  return (
    <Fragment>
      <Button onClick={onOpen} sx={{ color: "#161616", minWidth: "unset !important", background: "rgba(71, 77, 164, 0.32)", marginRight: "5px", borderRadius: "6px", padding: "10.5px", "&:hover": { color: "#161616", background: "rgba(71, 77, 164, 0.6)" }, "& svg": { width: "20px", height: "20px" } }}>{t("ADD_FARM")}</Button>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
        <DialogContent sx={{ padding: "0px !important" }}>
          <FarmAdd {...props} onClose={onClose} />
        </DialogContent>
      </Dialog>
    </Fragment>
  );
};

export default ModalFarmAdd;
