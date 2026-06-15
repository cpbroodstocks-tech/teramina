import type { ReactNode } from "react";
import { Button, Paper, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

type PageFilterBarProps = {
  children?: ReactNode;
  dirty?: boolean;
  disabled?: boolean;
  onReset?: () => void;
  title?: string;
};

const PageFilterBar = ({ children, dirty = false, disabled = false, onReset, title }: PageFilterBarProps) => {
  const { t } = useTranslation();

  return (
    <Paper component="section" variant="outlined" sx={{ p: 1.5, mb: 2 }} aria-label={title || t("PAGE_FILTERS")}>
      <Stack direction={{ xs: "column", md: "row" }} spacing={1.25} sx={{ alignItems: { md: "center" } }}>
        {title && <Typography variant="subtitle2" sx={{ mr: 0.5 }}>{title}</Typography>}
        <Stack direction={{ xs: "column", sm: "row" }} spacing={1} useFlexGap sx={{ flex: 1, flexWrap: "wrap" }}>
          {children}
        </Stack>
        <Stack direction="row" spacing={1}>
          <Button type="submit" variant="contained" disabled={!dirty || disabled}>
            {t("APPLY_FILTER")}
          </Button>
          {onReset && (
            <Button type="button" variant="text" onClick={onReset} disabled={!dirty}>
              {t("RESET_FILTER")}
            </Button>
          )}
        </Stack>
      </Stack>
    </Paper>
  );
};

export default PageFilterBar;
