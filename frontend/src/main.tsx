import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { Toaster } from "sonner";

import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>

    <BrowserRouter>

      <App />

      <Toaster
        richColors
        position="top-right"
        expand={false}
        closeButton
        duration={3000}
      />

    </BrowserRouter>

  </React.StrictMode>
);