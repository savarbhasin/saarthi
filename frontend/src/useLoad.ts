import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "./api";

// Loads one API resource; a 401 anywhere sends the user to sign in.
export function useLoad<T>(path: string) {
  const navigate = useNavigate();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    try {
      setData(await api<T>(path));
      setError("");
    } catch (exc) {
      if (exc instanceof ApiError && exc.status === 401) navigate("/login", { replace: true });
      else setError(exc instanceof Error ? exc.message : "Something went wrong.");
    }
  }, [path, navigate]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { data, error, reload };
}
