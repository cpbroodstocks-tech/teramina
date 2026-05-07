import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(() => ({
  containerTables: {
    // auto-size: header ~56px + up to 8 rows × 44px = ~408px max
    height: "410px",
  },
  columnHeaderCustom: {
    backgroundColor: "#F5F5F5",
  },
  virtualScrollerRenderZoneCustom: {
    width: "100% !important",
  },
  columnHeaderTitleContainerCustom: {
    justifyContent: "flex-start",
  },
  columnHeadersInnerCustom: {
    width: "100% !important",
  },
  columnHeaderRowCustom: {
    width: "100% !important",
  },
  rowCustom: {
    "&:hover": {
      backgroundColor: "#f9fafb",
    },
  },
}));

export { useStyles };
