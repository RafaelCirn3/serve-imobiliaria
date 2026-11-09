import { environment } from '@env/environment';

/** Uploaded media always follows the API origin, avoiding stale hosts and HTTP mixed content. */
export function mediaUrl(source: string | null | undefined): string {
  if (!source) return '';
  const origin = /^https?:\/\//.test(environment.apiUrl) ? new URL(environment.apiUrl).origin : '';
  if (source.startsWith('/media/')) return origin + source;
  if (/^https?:\/\//.test(source)) {
    try { const url = new URL(source); if (url.pathname.startsWith('/media/')) return origin + url.pathname + url.search; } catch { return ''; }
  }
  return source;
}
