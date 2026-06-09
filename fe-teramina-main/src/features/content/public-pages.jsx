import { Link, useParams } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { MdArrowForward } from "react-icons/md";
import { useContentItem, useContentItems, useDownloadContentPdf, useMyContentItems } from "./queries";
import { contentFallbacks } from "./catalog";

const contentStatus = (item) => item.access_status === "free" ? "free" : item.access_status || item.access_level;

const ContentCard = ({ item }) => {
  const status = contentStatus(item);
  const accessible = status === "free" || status === "granted";

  return (
    <Paper
      variant="outlined"
      sx={{
        height: "100%",
        p: { xs: 2, md: 2.5 },
        borderColor: "#e2e8f0",
        borderRadius: 1,
        transition: "border-color 160ms ease, box-shadow 160ms ease",
        "&:hover": {
          borderColor: "primary.main",
          boxShadow: "0 4px 14px rgba(71, 77, 164, 0.08)",
        },
      }}
    >
      <Stack gap={1.5} sx={{ height: "100%" }}>
        <Stack direction="row" gap={0.75} sx={{ flexWrap: "wrap" }}>
          <Chip size="small" label={item.category} />
          <Chip size="small" variant="outlined" label={(item.language || "en").toUpperCase()} />
          <Chip size="small" variant="outlined" label={item.variant_type || "master"} />
          <Chip size="small" color={accessible ? "success" : "default"} variant="outlined" label={status} />
        </Stack>
        <Box>
          <Typography variant="h6" fontWeight={700} sx={{ lineHeight: 1.35, mb: 0.75 }}>
            {item.title}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.55 }}>
            {item.summary}
          </Typography>
        </Box>
        <Stack direction="row" gap={0.75} sx={{ flexWrap: "wrap" }}>
          {(item.tags || []).map((tag) => <Chip key={tag} size="small" variant="outlined" label={tag} />)}
        </Stack>
        <Button
          component={Link}
          to={`/knowledge/${item.slug}`}
          variant="outlined"
          endIcon={<MdArrowForward />}
          sx={{ alignSelf: "flex-start", mt: "auto" }}
        >
          View
        </Button>
      </Stack>
    </Paper>
  );
};

export const KnowledgePage = () => {
  const { data = [], isLoading, isError } = useContentItems();
  const items = data.length ? data : contentFallbacks;

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Stack gap={2} sx={{ mb: 4 }}>
        <Typography variant="h3" fontWeight={700}>Knowledge Library</Typography>
        <Typography color="text.secondary" sx={{ maxWidth: 760 }}>
          Operational shrimp aquaculture SOPs, guides, templates, and decision frameworks connected to Teramina&apos;s advisory workflow.
        </Typography>
        {isError && <Alert severity="info">Showing starter library materials while the content API is unavailable.</Alert>}
      </Stack>
      {isLoading ? (
        <CircularProgress />
      ) : (
        <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" } }}>
          {items.map((item) => <ContentCard item={item} key={item.slug} />)}
        </Box>
      )}
    </Container>
  );
};

export const ContentDetailPage = () => {
  const { slug = "" } = useParams();
  const token = localStorage.getItem("authentication");
  const { data } = useContentItem(slug, !!token);
  const downloadPdf = useDownloadContentPdf();
  const fallback = contentFallbacks.find((item) => item.slug === slug);
  const item = data || fallback;

  if (!item) {
    return (
      <Container maxWidth="md" sx={{ py: 6 }}>
        <Alert severity="error">Content not found.</Alert>
      </Container>
    );
  }

  const locked = item.access_status === "locked" || item.access_status === "expired";
  const downloadPdfFile = async () => {
    const blob = await downloadPdf.mutateAsync({ slug: item.slug, authed: !!token });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `${item.slug}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Stack gap={2}>
        <Button component={Link} to="/knowledge" sx={{ alignSelf: "flex-start" }}>Back to Knowledge</Button>
        <Stack direction="row" gap={1} sx={{ flexWrap: "wrap" }}>
          <Chip label={item.category} />
          <Chip variant="outlined" label={item.language || "en"} />
          <Chip variant="outlined" label={item.variant_type || "master"} />
          <Chip variant="outlined" label={item.access_status === "free" ? "free" : item.access_status || item.access_level} />
        </Stack>
        <Typography variant="h3" fontWeight={700}>{item.title}</Typography>
        <Typography color="text.secondary">{item.summary}</Typography>
        {locked ? (
          <Alert
            severity="info"
            action={<Button component={Link} to="/services" color="inherit">Request Access</Button>}
          >
            This material requires paid or client access. Manual access is granted after purchase or advisory engagement.
          </Alert>
        ) : (
          <Paper variant="outlined" sx={{ p: 3 }}>
            <Typography sx={{ whiteSpace: "pre-wrap" }}>{item.body_markdown || "Document file access will appear here when attached."}</Typography>
            {item.file_url && (
              <Button href={item.file_url} target="_blank" rel="noreferrer" variant="contained" sx={{ mt: 2 }}>
                Open File
              </Button>
            )}
            <Button
              onClick={downloadPdfFile}
              variant="outlined"
              sx={{ mt: 2, ml: item.file_url ? 1 : 0 }}
              disabled={downloadPdf.isPending}
            >
              {downloadPdf.isPending ? "Preparing PDF..." : "Download PDF"}
            </Button>
          </Paper>
        )}
      </Stack>
    </Container>
  );
};

export const DashboardLibraryPage = () => {
  const { data = [], isLoading, isError } = useMyContentItems();

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        gap={2}
        sx={{ mb: 3, justifyContent: "space-between", alignItems: { sm: "flex-end" } }}
      >
        <Box>
          <Typography variant="h4" fontWeight={700}>Library</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Free and manually granted Teramina operating documents.
          </Typography>
        </Box>
        {!isLoading && !isError && data.length > 0 && (
          <Chip variant="outlined" label={`${data.length} ${data.length === 1 ? "document" : "documents"}`} />
        )}
      </Stack>
      {isError && <Alert severity="error">Failed to load library access.</Alert>}
      {isLoading ? (
        <Stack direction="row" gap={1} sx={{ alignItems: "center", py: 2 }}>
          <CircularProgress size={20} />
          <Typography variant="body2" color="text.secondary">Loading library...</Typography>
        </Stack>
      ) : data.length ? (
        <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" }, pb: 3 }}>
          {data.map((item) => <ContentCard item={item} key={item.slug} />)}
        </Box>
      ) : (
        <Alert severity="info">No paid library access has been granted yet.</Alert>
      )}
    </Container>
  );
};
