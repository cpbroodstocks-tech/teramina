import { useState } from "react";

const useModal = () => {
  const [open, setOpen] = useState(false);
  return {
    open,
    onOpen: () => setOpen(true),
    onClose: () => setOpen(false),
  };
};

export { useModal };
