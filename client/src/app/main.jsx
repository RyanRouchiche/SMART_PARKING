import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "@fontsource/hanken-grotesk/400.css";
import "@fontsource/hanken-grotesk/500.css";
import "@fontsource/hanken-grotesk/700.css";
import "@fontsource/hanken-grotesk/800.css";
import "../shared/styles/app.css";
import App from "./App.jsx";
import { AuthProvider } from "../features/auth/index.js";
import { LanguageProvider } from "../shared/i18n.jsx";
import { FeedbackProvider } from "../shared/ui/Feedback.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <LanguageProvider>
        <FeedbackProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </FeedbackProvider>
      </LanguageProvider>
    </BrowserRouter>
  </StrictMode>
);
