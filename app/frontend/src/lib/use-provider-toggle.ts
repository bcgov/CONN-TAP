import { useState } from "react";

export function useProviderToggle(initial: readonly string[]) {
  const [activeProviders, setActiveProviders] = useState<Set<string>>(() => new Set(initial));

  const toggleProvider = (traceName: string) => {
    setActiveProviders((prev) => {
      const next = new Set(prev);
      if (next.has(traceName)) next.delete(traceName);
      else next.add(traceName);
      return next;
    });
  };

  return { activeProviders, toggleProvider };
}
