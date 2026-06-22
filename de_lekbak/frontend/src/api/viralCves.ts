import { apiGet, apiPost } from "@/api/client";
import type { ViralCveRankingResponse, ViralCveRefreshResponse } from "@/types/viralCve";

export function fetchViralCves(): Promise<ViralCveRankingResponse> {
  return apiGet<ViralCveRankingResponse>("/viral-cves");
}

export function refreshViralCves(): Promise<ViralCveRefreshResponse> {
  return apiPost<ViralCveRefreshResponse>("/viral-cves/refresh");
}
