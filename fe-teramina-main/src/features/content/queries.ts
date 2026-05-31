import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { axios } from "helper/axios";

export const contentKeys = {
  items: ["content-items"] as const,
  item: (slug: string, authed = false) => ["content-item", slug, authed] as const,
  myItems: ["content-my-items"] as const,
  adminItems: ["content-admin-items"] as const,
  adminItem: (contentId: string) => ["content-admin-item", contentId] as const,
  adminRevisions: (contentId: string) => ["content-admin-revisions", contentId] as const,
  adminAccess: ["content-admin-access"] as const,
};

export const useContentItems = () =>
  useQuery({
    queryKey: contentKeys.items,
    queryFn: () => axios.get("/content/items").then((r: any) => r?.payload?.items ?? []),
    retry: false,
  });

export const useContentItem = (slug: string, authed = false) =>
  useQuery({
    queryKey: contentKeys.item(slug, authed),
    queryFn: () =>
      axios
        .get(authed ? `/content/my-items/${slug}` : `/content/items/${slug}`)
        .then((r: any) => r?.payload?.item ?? null),
    enabled: !!slug,
    retry: false,
  });

export const useDownloadContentPdf = () =>
  useMutation({
    mutationFn: ({ slug, authed }: { slug: string; authed?: boolean }) =>
      axios
        .get(authed ? `/content/my-items/${slug}/pdf` : `/content/items/${slug}/pdf`, { responseType: "blob" })
        .then((response: any) => (response instanceof Blob ? response : response.data)),
  });

export const useMyContentItems = () =>
  useQuery({
    queryKey: contentKeys.myItems,
    queryFn: () => axios.get("/content/my-items").then((r: any) => r?.payload?.items ?? []),
  });

export const useAdminContentItems = (enabled = true) =>
  useQuery({
    queryKey: contentKeys.adminItems,
    queryFn: () => axios.get("/content/admin/items").then((r: any) => r?.payload?.items ?? []),
    enabled,
  });

export const useAdminContentAccess = (enabled = true) =>
  useQuery({
    queryKey: contentKeys.adminAccess,
    queryFn: () => axios.get("/content/admin/access").then((r: any) => r?.payload?.access ?? []),
    enabled,
  });

export const useAdminContentItem = (contentId: string, enabled = true) =>
  useQuery({
    queryKey: contentKeys.adminItem(contentId),
    queryFn: () => axios.get(`/content/admin/items/${contentId}`).then((r: any) => r?.payload?.item ?? null),
    enabled: enabled && !!contentId,
  });

export const useAdminContentRevisions = (contentId: string, enabled = true) =>
  useQuery({
    queryKey: contentKeys.adminRevisions(contentId),
    queryFn: () => axios.get(`/content/admin/items/${contentId}/revisions`).then((r: any) => r?.payload?.revisions ?? []),
    enabled: enabled && !!contentId,
  });

export const useCreateContentItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      title: string;
      slug: string;
      summary?: string;
      category: string;
      tags?: string[];
      language?: string;
      variant_group_id?: string;
      variant_type?: string;
      source_content_id?: string;
      content_type?: string;
      access_level?: string;
      body_markdown?: string;
      file_url?: string;
      version?: string;
      status?: string;
      change_note?: string;
    }) => axios.post("/content/items", payload).then((r: any) => r?.payload?.item ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contentKeys.items });
      queryClient.invalidateQueries({ queryKey: contentKeys.adminItems });
    },
  });
};

export const useUpdateContentItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      contentId,
      payload,
    }: {
      contentId: string;
      payload: {
        title?: string;
        summary?: string;
        category?: string;
        tags?: string[];
        language?: string;
        variant_group_id?: string;
        variant_type?: string;
        source_content_id?: string;
        content_type?: string;
        access_level?: string;
        body_markdown?: string;
        file_url?: string;
        version?: string;
        status?: string;
        change_note?: string;
      };
    }) => axios.patch(`/content/items/${contentId}`, payload).then((r: any) => r?.payload?.item ?? null),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contentKeys.items });
      queryClient.invalidateQueries({ queryKey: contentKeys.adminItems });
      queryClient.invalidateQueries({ queryKey: contentKeys.adminItem(variables.contentId) });
      queryClient.invalidateQueries({ queryKey: contentKeys.adminRevisions(variables.contentId) });
    },
  });
};

export const useTransitionContentWorkflow = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      contentId,
      payload,
    }: {
      contentId: string;
      payload: {
        status: string;
        review_note?: string;
      };
    }) => axios.post(`/content/items/${contentId}/workflow`, payload).then((r: any) => r?.payload?.item ?? null),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contentKeys.items });
      queryClient.invalidateQueries({ queryKey: contentKeys.adminItems });
      queryClient.invalidateQueries({ queryKey: contentKeys.adminItem(variables.contentId) });
      queryClient.invalidateQueries({ queryKey: contentKeys.adminRevisions(variables.contentId) });
    },
  });
};

export const useGrantContentAccess = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { user_id: string; content_id: string; access_source?: string; expires_at?: string | null }) =>
      axios.post("/content/access", payload).then((r: any) => r?.payload?.access ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contentKeys.adminAccess });
      queryClient.invalidateQueries({ queryKey: contentKeys.myItems });
    },
  });
};
