"use client";

import { useEffect } from "react";

export function DevelopmentDiagnostics() {
  useEffect(() => {
    const isEnabled =
      process.env.NODE_ENV === "development" &&
      process.env.NEXT_PUBLIC_DISABLE_REACT_DEVTOOLS !== "1";

    if (!isEnabled) {
      return;
    }

    void import("react-grab");
    void import("react-scan").then(({ scan }) => scan());
  }, []);

  return null;
}
