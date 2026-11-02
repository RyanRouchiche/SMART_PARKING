import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "@fontsource/hanken-grotesk/400.css";
import "@fontsource/hanken-grotesk/500.css";
import "@fontsource/hanken-grotesk/700.css";
import "@fontsource/hanken-grotesk/800.css";
import "./styles/app.css";
import App from "./App.jsx";
import { AuthProvider } from "./auth.jsx";
import { LanguageProvider } from "./i18n.jsx";
import { FeedbackProvider } from "./components/Feedback.jsx";

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
