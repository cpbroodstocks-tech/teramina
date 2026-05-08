import { Fragment } from "react";
import { Button, Dialog, DialogContent } from "@mui/material";
import { useToastStore } from "store/toast.store";
import { useAddCycle } from "features/cycle/queries";
import { useParams } from "react-router-dom";
import NewCycle from "features/farm/new-cycle";
import { useNewCycleForm } from "features/farm/new-cycle/hooks";
import dayjs from "dayjs";
import { useModal } from "hooks/useModal";
import { useTranslation } from "react-i18next";

const CycleAdd = ({ onClose }) => {
  const { t } = useTranslation();
  const { pond_id } = useParams();
  const { setToast: toast } = useToastStore();
  const { mutateAsync } = useAddCycle();

  const handleSubmit = async (value) => {
    try {
      const date = dayjs(value.date).format("MM/DD/YYYY");
      await mutateAsync({ pond_id, name: value.name, start_date: date });
      await onClose();
      toast({ open: true, variant: "success", text: t("ADD_DATA_SUCCESS_MESSAGE") });
    } catch {
      toast({ open: true, variant: "error", text: t("ADD_DATA_FAILED_MESSAGE") });
    }
  };

  const form = useNewCycleForm({
    onSubmit: handleSubmit,
  });

  return <NewCycle isModalComponent form={form} />;
};

const ModalCycleAdd = (props) => {
  const { t } = useTranslation();
  const { open, onOpen, onClose } = useModal();
  return (
    <Fragment>
      <Button onClick={onOpen} sx={{ color: "#161616", minWidth: "unset !important", background: "rgba(71, 77, 164, 0.32)", marginRight: "5px", borderRadius: "6px", padding: "10.5px", "&:hover": { color: "#161616", background: "rgba(71, 77, 164, 0.6)" }, "& svg": { width: "20px", height: "20px" } }}>{t("ADD_CYCLE")}</Button>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
        <DialogContent sx={{ padding: "0px !important" }}>
          <CycleAdd {...props} onClose={onClose} />
        </DialogContent>
      </Dialog>
    </Fragment>
  );
};

export default ModalCycleAdd;
