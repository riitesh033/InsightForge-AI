import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";

import "./styles/index.css";

import App from "./App";
import { ThemeProvider } from "@/context/ThemeContext";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <App />
        <Toaster
          richColors
          position="top-right"
          closeButton
        />
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>
);