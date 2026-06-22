import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchViralCves, refreshViralCves } from "@/api/viralCves";

export function useViralCves() {
  return useQuery({
    queryKey: ["viral-cves"],
    queryFn: fetchViralCves,
  });
}

export function useRefreshViralCves() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: refreshViralCves,
    onSuccess: (data) => {
      queryClient.setQueryData(["viral-cves"], data.rankings);
    },
  });
}
