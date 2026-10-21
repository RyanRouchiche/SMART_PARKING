import { Fragment, useState } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
import { Navigation, Pagination } from "swiper/modules";
import css from "../styles/camera.css?inline";
import Navbar from "../components/Navbar.jsx";
import { useModal } from "../components/Modal.jsx";
import { api } from "../api.js";
import { useT } from "../i18n.jsx";
import camImage from "../assets/cam.png";

const MAX_CAMERAS = 10;
const FIELDS = [
  ["area", "Zone (area):", "Ex: 1"],
  ["ref", "Reference (ref):", "Ex: CAM01"],
  ["path", "Chemin RTSP/HTTP (path):", "Ex: rtsp://..."],
];

const newCamera = (id) => ({ id, area: "", ref: "", path: "" });

const styles = {
  card: { position: "relative", padding: "50px", margin: "1rem" },
  icon: { position: "absolute", top: "50%", left: "0%", transform: "translate(0%, -50%)" },
  image: { width: "80px", cursor: "pointer" },
  title: { color: "#fff", position: "absolute", top: "80%", left: "20%", whiteSpace: "nowrap" },
  buttons: {
    position: "absolute", width: "100%", height: "100%", top: 0, left: 0, display: "flex",
    flexDirection: "column", justifyContent: "space-between", alignItems: "flex-end",
    padding: "10px", pointerEvents: "none",
  },
  delete: {
    position: "absolute", top: "10%", right: "10%", border: "none", background: "rgba(255, 0, 0, 0.7)",
    color: "#fff", borderRadius: "50%", cursor: "pointer", pointerEvents: "auto",
  },
};

export default function CameraSetup() {
  const t = useT();
  const modal = useModal();
  const [cameras, setCameras] = useState([newCamera(0)]);
  const [swiper, setSwiper] = useState(null);

  const addCamera = () => {
    const used = new Set(cameras.map((c) => c.id));
    let id = 0;
    while (used.has(id)) id++;
    setCameras([...cameras, newCamera(id)].sort((a, b) => a.id - b.id));
  };

  const removeCamera = async (id) => {
    if (await modal.confirm(t("Are you sure you want to delete this slide?"))) {
      setCameras(cameras.filter((c) => c.id !== id));
    }
  };

  const updateCamera = (id, name, value) =>
    setCameras(cameras.map((c) => (c.id === id ? { ...c, [name]: value } : c)));

  const submit = async () => {
    if (!(await modal.confirm(t("Do you want to validate and submit all cameras?")))) {
      return;
    }
    const payload = cameras.map(({ area, ref, path }) => ({
      area: area.trim(),
      ref: ref.trim(),
      path: path.trim(),
    }));
    if (payload.some((c) => !c.area || !c.ref || !c.path)) {
      modal.notify(t("Please fill in all fields for each camera."));
      return;
    }
    const res = await api("/cameras/", { method: "POST", body: payload });
    if (res.status === 403) {
      modal.notify(t("Only admin"));
    } else if (res.ok) {
      modal.notify(t("Cameras added successfully!"));
      setCameras([newCamera(0)]);
      swiper?.slideTo(0);
    } else {
      modal.notify(t("Error submitting cameras."));
    }
  };

  const full = cameras.length >= MAX_CAMERAS;

  return (
    <>
      <style>{css}</style>
      <Navbar />

      <Swiper
        modules={[Navigation, Pagination]}
        navigation
        pagination={{ clickable: true }}
        autoHeight
        onSwiper={setSwiper}
      >
        {cameras.map((camera) => (
          <SwiperSlide key={camera.id}>
            <div className="main__content">
              <div className="formContainer">
                <div className="camera-form">
                  <h1>
                    {camera.id === 0
                      ? t("Camera Configuration")
                      : `${t("Camera Configuration")} N_${camera.id}`}
                  </h1>
                  {FIELDS.map(([name, label, placeholder]) => (
                    <Fragment key={name}>
                      <label>{label}</label>
                      <input
                        type="text"
                        placeholder={placeholder}
                        autoComplete="off"
                        value={camera[name]}
                        onChange={(e) => updateCamera(camera.id, name, e.target.value)}
                      />
                    </Fragment>
                  ))}
                </div>
              </div>
            </div>
          </SwiperSlide>
        ))}
      </Swiper>

      <div className="right-section" id="top_section">
        <button className="main__btn" onClick={addCamera} disabled={full}>
          {full ? t("Max slides reached") : t("Add")}
        </button>
        <button className="main__btn" onClick={submit}>
          {t("Validate and send")}
        </button>
      </div>

      <div className="right-section" id="bottom_section">
        {cameras.map((camera, index) => (
          <div className="services__card slide-control" style={styles.card} key={camera.id}>
            <div style={styles.icon}>
              <img src={camImage} style={styles.image} onClick={() => swiper?.slideTo(index)} />
            </div>
            <h2 style={styles.title}>Cam {camera.id}</h2>
            <div className="card-buttons" style={styles.buttons}>
              {camera.id !== 0 && (
                <button style={styles.delete} onClick={() => removeCamera(camera.id)}>
                  ✕
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
