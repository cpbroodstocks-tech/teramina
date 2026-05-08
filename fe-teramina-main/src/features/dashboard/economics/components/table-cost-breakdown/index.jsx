import * as React from "react";
import { DataGrid } from "@mui/x-data-grid";
import { useStyles } from "widgets/economics/components/table-cost-breakdown/styles";

const LABEL_MAP = {
  feed: "Feed",
  probiotics: "Probiotics",
  energy: "Energy",
  labor: "Labor",
  bonuss: "Bonus",
  bonus: "Bonus",
  harvest: "Harvest",
  other: "Other",
  seed: "Seed (PL)",
};

const formatLabel = (raw) => {
  if (!raw) return "";
  return LABEL_MAP[raw] ?? raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
};

const columns = [
  {
    field: "labelColor",
    headerName: "",
    width: 36,
    sortable: false,
    renderCell: (params) => (
      <span
        style={{
          display: "inline-block",
          width: 12,
          height: 12,
          borderRadius: "50%",
          backgroundColor: params.value,
          flexShrink: 0,
        }}
      />
    ),
  },
  {
    field: "name",
    headerName: "Item",
    flex: 1,
    sortable: false,
    valueFormatter: (params) => formatLabel(params.value),
  },
  {
    field: "value",
    headerName: "Cost (IDR)",
    flex: 1.4,
    sortable: false,
    align: "right",
    headerAlign: "right",
  },
];

const TableCostBreakdown = ({ data, color }) => {
  const { classes: styles } = useStyles();
  const rows = data.map((row, key) => ({ ...row, labelColor: color[key], id: key }));
  return (
    <div className={styles.containerTables}>
      <DataGrid
        columns={columns}
        hideFooterPagination
        hideFooterSelectedRowCount
        hideFooter
        rows={rows}
        getRowId={(row) => row.id}
        disableColumnSelector
        disableDensitySelector
        disableColumnMenu
        rowHeight={44}
        classes={{
          columnHeaders: styles.columnHeaderCustom,
          row: styles.rowCustom,
          virtualScrollerRenderZone: styles.virtualScrollerRenderZoneCustom,
          columnHeaderTitleContainer: styles.columnHeaderTitleContainerCustom,
          columnHeader: styles.columnHeaderCustom,
          columnHeadersInner: styles.columnHeadersInnerCustom,
          columnHeaderRow: styles.columnHeaderRowCustom,
        }}
      />
    </div>
  );
};

export default TableCostBreakdown;
