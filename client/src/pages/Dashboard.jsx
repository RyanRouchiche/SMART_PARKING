import { useNavigate } from "react-router-dom";
import css from "../styles/dashboard.css?inline";
import Navbar from "../components/Navbar.jsx";
import { useAuth } from "../auth.jsx";
import { useT } from "../i18n.jsx";
import heroImage from "../assets/undraw_pic1.svg";
import databaseImage from "../assets/database.jpg";
import cameraImage from "../assets/camera.webp";
import spotsImage from "../assets/spots.jpg";
import parkingImage from "../assets/parking.jpeg";

const SERVICES = [
  { path: "/management", title: "Dashboard", text: "Manage your users database", image: databaseImage },
  { path: "/setup", title: "Setup", text: "Add/Delete cameras from your database", image: cameraImage },
  { path: "/lcd", title: "LCD", text: "Parking data displayed on LCD", image: spotsImage },
  { path: "/spots", title: "Initialization", text: "you can manually change your parking spots!", image: parkingImage },
];

const FOOTER = [
  [
    ["About us", ["How it works", "Testimonals", "Carrers", "Investements", "Terms of Service"]],
    ["Contact us", ["Contact", "Support", "Destinations", "Sponsorships"]],
  ],
  [
    ["Video", ["Submit video", "Ambasadors", "Agency", "Influencer"]],
    ["Social Media", ["Instagram", "Facebook", "Youtube", "Twitter"]],
  ],
];

export default function Dashboard() {
  const t = useT();
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <>
      <style>{css}</style>
      <Navbar />

      <div className="main">
        <div className="main__container">
          <div className="main__content">
            <h1>{t("Welcome,")}</h1>
            <h2>{user.username}</h2>
            <p>{t("View your parking simulation.")}</p>
            <button className="main__btn" onClick={() => navigate("/parking")}>
              <a>{t("View Status")}</a>
            </button>
          </div>
          <div className="main__img--container">
            <img src={heroImage} alt="" id="main__img" />
          </div>
        </div>
      </div>

      <div className="services">
        <h1>{t("What are we offering ?")}</h1>
        <div className="services__container">
          {SERVICES.map((service) => (
            <a key={service.path} onClick={() => navigate(service.path)}>
              <div
                className="services__card"
                style={{
                  backgroundImage: `linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, rgba(17, 17, 17, 0.6) 100%), url('${service.image}')`,
                }}
              >
                <h2>{t(service.title)}</h2>
                <p>{t(service.text)}</p>
                <button>{t("Get Started")}</button>
              </div>
            </a>
          ))}
        </div>
      </div>

      <div className="footer__container">
        <div className="footer__links">
          {FOOTER.map((wrapper, i) => (
            <div className="footer__link--wrapper" key={i}>
              {wrapper.map(([title, links]) => (
                <div className="footer__link--items" key={title}>
                  <h2>{t(title)}</h2>
                  {links.map((link) => (
                    <a href="/" key={link}>
                      {t(link)}
                    </a>
                  ))}
                </div>
              ))}
            </div>
          ))}
        </div>
        <div className="social__media">
          <div className="social__media--wrap">
            <div className="footer__logo">
              <a id="footer__logo">PARKING</a>
            </div>
            <p className="website__rights">o PARKING {t("2025.All rights reserved")}</p>
          </div>
        </div>
      </div>
    </>
  );
}
