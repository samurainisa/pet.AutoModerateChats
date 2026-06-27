const explicitOrigin = (import.meta.env.VITE_API_ORIGIN as string | undefined)?.trim();
const defaultOrigin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5000";

export const apiOrigin = explicitOrigin && explicitOrigin.length > 0 ? explicitOrigin : defaultOrigin;
