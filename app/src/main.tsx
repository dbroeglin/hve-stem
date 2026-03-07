import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@primer/primitives/dist/css/functional/themes/light.css";
import "@primer/primitives/dist/css/functional/themes/dark.css";
import "@primer/primitives/dist/css/base/motion/motion.css";
import "@primer/primitives/dist/css/base/size/size.css";
import "@primer/primitives/dist/css/base/typography/typography.css";
import { ThemeProvider, BaseStyles } from "@primer/react";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider colorMode="auto" nightScheme="dark" dayScheme="light">
      <BaseStyles>
        <App />
      </BaseStyles>
    </ThemeProvider>
  </StrictMode>,
);
