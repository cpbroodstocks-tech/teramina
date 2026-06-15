import type { ReactNode } from "react";
import { Box, Stack, Typography } from "@mui/material";

type PageHeaderProps = {
  title: ReactNode;
  description?: ReactNode;
  eyebrow?: ReactNode;
  actions?: ReactNode;
};

const PageHeader = ({ title, description, eyebrow, actions }: PageHeaderProps) => (
  <Stack
    component="header"
    direction={{ xs: "column", sm: "row" }}
    spacing={2}
    sx={{ alignItems: { sm: "flex-start" }, justifyContent: "space-between", mb: 2.5 }}
  >
    <Box sx={{ minWidth: 0, maxWidth: 760 }}>
      {eyebrow && (
        <Typography variant="overline" color="primary.main" sx={{ fontWeight: 700 }}>
          {eyebrow}
        </Typography>
      )}
      <Typography component="h1" variant="h4" sx={{ fontWeight: 700, letterSpacing: "-0.02em" }}>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          {description}
        </Typography>
      )}
    </Box>
    {actions && <Box sx={{ flexShrink: 0 }}>{actions}</Box>}
  </Stack>
);

export default PageHeader;
