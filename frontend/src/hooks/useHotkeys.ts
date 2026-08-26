import { useEffect } from "react";

type HandlerMap = Record<string, () => void>;

export function useHotkeys(handlers: HandlerMap) {
  useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      const handler = handlers[key];
      if (handler) {
        event.preventDefault();
        handler();
      }
    };
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, [handlers]);
}
