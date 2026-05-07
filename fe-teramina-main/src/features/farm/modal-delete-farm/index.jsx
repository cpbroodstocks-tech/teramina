import { Fragment, useState } from "react";
import { Button } from "@mui/material";
import { useStyles } from "features/farm/modal-delete-farm/styles";
import ConfirmDelete from "components/confirm-delete";
import { useDeleteFarm } from "features/farm/queries";
import { useToastStore } from "store/toast.store";
import { useTranslation } from "react-i18next";

const ModalDeleteFarm = ({ data }) => {
  const { t } = useTranslation();
  const { setToast: toast } = useToastStore();
  const { mutateAsync } = useDeleteFarm();
  const { classes: styles } = useStyles();

  const [openConfirmDelete, setOpenConfirmDelete] = useState(() => false);

  const handleDelete = async () => {
    try {
      setOpenConfirmDelete(false);
      await mutateAsync(data._id);
      toast({ open: true, variant: "success", text: t("DELETE_DATA_SUCCESS_MESSAGE") });
    } catch {
      toast({ open: true, variant: "error", text: t("DELETE_DATA_FAILED_MESSAGE") });
    }
  };

  return (
    <Fragment>
      <Button
        className={styles.btnDelete}
        onClick={() => setOpenConfirmDelete(true)}
      >
        <svg
          width="26"
          height="28"
          viewBox="0 0 26 28"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M23.041 10.5059C23.041 10.5059 22.2725 20.0377 21.8267 24.0528C21.6144 25.9705 20.4298 27.0941 18.4895 27.1295C14.7971 27.196 11.1004 27.2003 7.40944 27.1225C5.54271 27.0843 4.37795 25.9464 4.1699 24.0627C3.72127 20.0122 2.95703 10.5059 2.95703 10.5059"
            stroke="#161616"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M25 5.93848H1"
            stroke="#161616"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M20.3785 5.93782C19.2675 5.93782 18.3108 5.15235 18.0928 4.06401L17.7489 2.34309C17.5366 1.54913 16.8177 1 15.9982 1H10.0074C9.188 1 8.46905 1.54913 8.25676 2.34309L7.91283 4.06401C7.69488 5.15235 6.73818 5.93782 5.6272 5.93782"
            stroke="#161616"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </Button>
      <ConfirmDelete
        open={openConfirmDelete}
        handleClose={() => setOpenConfirmDelete(false)}
        handleConfirmed={() => handleDelete()}
        message="DELETE_CONFIRM_MESSAGE"
      />
    </Fragment>
  );
};

export default ModalDeleteFarm;
