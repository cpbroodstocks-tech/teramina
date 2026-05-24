import { Fragment } from "react";
import { Button, Dialog, DialogContent } from "@mui/material";
import { useToastStore } from "store/toast.store";
import { useAddPond } from "features/pond/queries";
import NewPond from "features/farm/new-pond";
import { useNewPondForm } from "features/farm/new-pond/hooks";
import { useParams } from "react-router-dom";
import { useModal } from "hooks/useModal";
import { useTranslation } from "react-i18next";

const PondAdd = ({ onClose }) => {
  const { t } = useTranslation();
  const { farm_id } = useParams();
  const { setToast: toast } = useToastStore();
  const { mutateAsync } = useAddPond();

  const handleSubmit = async (value) => {
    try {
      await mutateAsync({
        farm_id,
        name: value.name,
        size: value.size,
        pond_construction: value.construction.value === "other" ? value.otherConstructionLabel : value.construction.label,
        pond_shape: value.shape.value === "other" ? value.otherShapeLabel : value.shape.label,
      });
      await onClose();
      toast({ open: true, variant: "success", text: t("ADD_DATA_SUCCESS_MESSAGE") });
    } catch {
      toast({ open: true, variant: "error", text: t("ADD_DATA_FAILED_MESSAGE") });
    }
  };

  const form = useNewPondForm({
    onSubmit: handleSubmit,
  });
  return <NewPond isModalComponent form={form} />;
};

const ModalPondAdd = (props) => {
  const { t } = useTranslation();
  const { open, onOpen, onClose } = useModal();
  return (
    <Fragment>
      <Button onClick={onOpen} sx={{ color: "#161616", minWidth: "unset !important", background: "rgba(71, 77, 164, 0.32)", marginRight: "5px", borderRadius: "6px", padding: "10.5px", "&:hover": { color: "#161616", background: "rgba(71, 77, 164, 0.6)" }, "& svg": { width: "20px", height: "20px" } }}>{t("ADD_POND")}</Button>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
        <DialogContent sx={{ padding: "0px !important" }}>
          <PondAdd {...props} onClose={onClose} />
        </DialogContent>
      </Dialog>
    </Fragment>
  );
};

export default ModalPondAdd;
