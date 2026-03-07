import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ThemeProvider, BaseStyles } from "@primer/react";
import "./index.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider colorMode="auto" nightScheme="dark" dayScheme="light">
      <BaseStyles>
        <App />
      </BaseStyles>
    </ThemeProvider>
  </StrictMode>,
);
