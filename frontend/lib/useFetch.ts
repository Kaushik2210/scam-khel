"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api";

export function useFetch<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!!path);
  const load = useCallback(() => {
    if (!path) return;
    setLoading(true);
    setError(null);
    api<T>(path)
      .then(setData)
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : "Unexpected error"))
      .finally(() => setLoading(false));
  }, [path]);
  useEffect(load, [load]);
  return { data, error, loading, reload: load };
}
