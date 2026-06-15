import type { ReactNode } from "react";
import { Card, CardActions, CardContent, Divider, Stack, Typography } from "@mui/material";

type Field<T> = {
  label: ReactNode;
  value: (item: T) => ReactNode;
};

type ResponsiveDataListProps<T> = {
  items: T[];
  fields: Field<T>[];
  getKey: (item: T, index: number) => string | number;
  renderActions?: (item: T) => ReactNode;
};

const ResponsiveDataList = <T,>({ items, fields, getKey, renderActions }: ResponsiveDataListProps<T>) => (
  <Stack spacing={1.5} sx={{ display: { xs: "flex", md: "none" } }}>
    {items.map((item, index) => (
      <Card key={getKey(item, index)} variant="outlined">
        <CardContent sx={{ display: "grid", gap: 1.25 }}>
          {fields.map((field, fieldIndex) => (
            <Stack key={fieldIndex} direction="row" spacing={2} sx={{ justifyContent: "space-between", alignItems: "baseline" }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                {field.label}
              </Typography>
              <Typography variant="body2" sx={{ textAlign: "right", overflowWrap: "anywhere" }}>
                {field.value(item)}
              </Typography>
            </Stack>
          ))}
        </CardContent>
        {renderActions && (
          <>
            <Divider />
            <CardActions sx={{ flexWrap: "wrap", justifyContent: "flex-end", gap: 0.5 }}>
              {renderActions(item)}
            </CardActions>
          </>
        )}
      </Card>
    ))}
  </Stack>
);

export default ResponsiveDataList;
