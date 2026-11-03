const NO_REFRESH = ["/auth/login/", "/auth/refresh/", "/auth/logout/"];

let refreshing = null;

function refreshSession() {
  refreshing ??= fetch("/api/auth/refresh/", {
    method: "POST",
    credentials: "include",
  })
    .then((res) => res.ok)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

export async function api(path, { method = "GET", body } = {}) {
  const options = {
    method,
    credentials: "include",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  };

  let res = await fetch(`/api${path}`, options);
  if (res.status === 401 && !NO_REFRESH.includes(path)) {
    if (await refreshSession()) {
      res = await fetch(`/api${path}`, options);
    }
    if (res.status === 401) {
      window.dispatchEvent(new Event("session-expired"));
    }
  }

  const data = res.status === 204 ? null : await res.json().catch(() => null);
  return { ok: res.ok, status: res.status, data };
}

export function openSocket(path) {
  const scheme = window.location.protocol === "https:" ? "wss" : "ws";
  return new WebSocket(`${scheme}://${window.location.host}/ws/${path}`);
}
