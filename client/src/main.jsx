import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { AuthProvider } from "./auth.jsx";
import { LanguageProvider } from "./i18n.jsx";
import { ModalProvider } from "./components/Modal.jsx";
import "swiper/css";
import "swiper/css/navigation";
import "swiper/css/pagination";
import "./styles/modal.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <LanguageProvider>
        <ModalProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </ModalProvider>
      </LanguageProvider>
    </BrowserRouter>
  </StrictMode>
);
