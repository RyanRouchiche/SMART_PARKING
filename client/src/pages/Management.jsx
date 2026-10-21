import { Fragment, useCallback, useEffect, useState } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
import { Navigation, Pagination } from "swiper/modules";
import css from "../styles/forms.css?inline";
import Navbar from "../components/Navbar.jsx";
import { useModal } from "../components/Modal.jsx";
import { api } from "../api.js";
import { useT } from "../i18n.jsx";

const EMPTY_GUEST = { username: "", password: "", email: "", first_name: "", last_name: "" };
const GUEST_FIELDS = [
  ["username", "text", "Username"],
  ["password", "password", "Password"],
  ["email", "email", "Email"],
  ["first_name", "text", "First Name"],
  ["last_name", "text", "Last Name"],
];

export default function Management() {
  const t = useT();
  const modal = useModal();
  const [guest, setGuest] = useState(EMPTY_GUEST);
  const [guestError, setGuestError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [users, setUsers] = useState([]);
  const [cameras, setCameras] = useState([]);

  const loadUsers = useCallback(async () => {
    const res = await api("/users/");
    if (res.status === 403) {
      modal.notify(t("Only admin"));
    } else if (res.ok) {
      setUsers(res.data.users);
    }
  }, [modal, t]);

  const loadCameras = useCallback(async () => {
    const res = await api("/cameras/");
    if (res.ok) {
      setCameras(res.data.cameras);
    } else if (res.status !== 403) {
      modal.notify(t("Error loading cameras."));
    }
  }, [modal, t]);

  useEffect(() => {
    loadUsers();
    loadCameras();
  }, [loadUsers, loadCameras]);

  useEffect(() => {
    const onStatus = ({ detail }) =>
      setUsers((list) =>
        list.map((u) => (u.id === detail.user_id ? { ...u, status: detail.status } : u))
      );
    window.addEventListener("user-status", onStatus);
    return () => window.removeEventListener("user-status", onStatus);
  }, []);

  const createGuest = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    const res = await api("/users/", { method: "POST", body: guest });
    setSubmitting(false);
    if (!res.ok) {
      setGuestError(t("Guest registration failed. Please check your credentials and try again."));
      return;
    }
    await modal.notify(t("Guest registration successful. Please confirm your email"));
    setGuest(EMPTY_GUEST);
    loadUsers();
  };

  const deleteUser = async (id) => {
    if (!(await modal.confirm(t("Are you sure you want to delete this user?")))) {
      return;
    }
    const res = await api(`/users/${id}/`, { method: "DELETE" });
    modal.notify(t(res.ok ? "User deleted successfully." : "Error: delete user."));
    if (res.ok) {
      loadUsers();
    }
  };

  const deleteCamera = async (id) => {
    if (!(await modal.confirm(t("Are you sure you want to delete this camera?")))) {
      return;
    }
    const res = await api(`/cameras/${id}/`, { method: "DELETE" });
    modal.notify(t(res.ok ? "Camera deleted successfully!" : "Error deleting camera."));
    if (res.ok) {
      loadCameras();
    }
  };

  return (
    <>
      <style>{css}</style>
      <Navbar />

      <Swiper modules={[Navigation, Pagination]} navigation pagination={{ clickable: true }} autoHeight>
        <SwiperSlide>
          <div className="main__content">
            <div className="formContainer">
              <div className="camera-form" id="guest">
                <h1>{t("Guest Management")}</h1>
                {guestError && (
                  <p className="error-message" style={{ display: "block" }}>
                    {guestError}
                  </p>
                )}
                <form onSubmit={createGuest}>
                  {GUEST_FIELDS.map(([name, type, label]) => (
                    <Fragment key={name}>
                      <label htmlFor={`guest-${name}`}>{t(label)}:</label>
                      <input
                        id={`guest-${name}`}
                        type={type}
                        required
                        autoComplete="off"
                        value={guest[name]}
                        onFocus={() => setGuestError("")}
                        onChange={(e) => setGuest({ ...guest, [name]: e.target.value })}
                      />
                    </Fragment>
                  ))}
                  <button type="submit" disabled={submitting}>
                    {t("Register Guest")}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </SwiperSlide>

        <SwiperSlide>
          <div className="main__content">
            <div className="formContainer">
              <div className="list-form" id="cams">
                <h2>{t("cams List")}</h2>
                <table id="cameraTable">
                  <thead>
                    <tr>
                      <th>reference</th>
                      <th>{t("area")} RTSP</th>
                      <th>{t("link")}</th>
                      <th>{t("Status")}</th>
                      <th>{t("Action")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cameras.map((camera) => (
                      <tr className="camera-item" key={camera.id}>
                        <td>{camera.ref}</td>
                        <td>{camera.area}</td>
                        <td>{camera.path}</td>
                        <td>{String(camera.is_active)}</td>
                        <td>
                          <button className="delete-cam-btn" onClick={() => deleteCamera(camera.id)}>
                            {t("Delete")}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </SwiperSlide>

        <SwiperSlide>
          <div className="main__content">
            <div className="formContainer">
              <div className="list-form" id="users">
                <h2>{t("Users List")}</h2>
                <table id="userTable">
                  <thead>
                    <tr>
                      <th>{t("Username")}</th>
                      <th>{t("Email")}</th>
                      <th>{t("First Name")}</th>
                      <th>{t("Last Name")}</th>
                      <th>{t("Status")}</th>
                      <th>{t("Action")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id}>
                        <td>{u.username}</td>
                        <td>{u.email}</td>
                        <td>{u.first_name}</td>
                        <td>{u.last_name}</td>
                        <td>{u.status}</td>
                        <td>
                          <button className="delete-user-btn" onClick={() => deleteUser(u.id)}>
                            {t("Delete")}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </SwiperSlide>
      </Swiper>
    </>
  );
}
