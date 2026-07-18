"use client";

import { ConfigProvider } from "antd";

export function ThemeProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: "#1A1C1E",
          colorError: "#BA1A1A",
          colorWarning: "#A06800",
          colorSuccess: "#1F6E2E",
          borderRadius: 4,
          fontFamily: "var(--font-public-sans), sans-serif",
        },
        components: {
          Button: { primaryColor: "#FFFFFF" },
        },
      }}
    >
      {children}
    </ConfigProvider>
  );
}
