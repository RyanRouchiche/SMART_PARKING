export async function scheduleStaticTokenRefresh() {
  setInterval(async () => {
    try {
      console.log("Attempting token refresh...");

      const res = await fetch("/auth/token/refresh/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        console.warn("Token refresh failed. Redirecting to login...");
        window.location.href = "/";
      } else {
        console.log("Token successfully refreshed.");
      }
    } catch (error) {
      console.error("Token refresh error:", error);
      window.location.href = "/";
    }
  }, 1680000);
}

export async function sendrequest(url, method) {
  try {
    const response = await fetch(url, {
      method: method,
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (response.status === 403) {
      alert("only admin");
    }

    if (response.status === 403) {
      alert("Only admin");
    }

    const result = await response.json();

    return {
      status: response.status,
      ok: response.ok,
      data: result,
    };
  } catch (error) {
    console.error("Error:", error);
  }
}

export function initwebsocketconn(wsschema) {
  const websocket = new WebSocket(
    `${wsschema}://${window.location.host}/ws/user-status/`
  );

  console.log("WebSocket connection established:", websocket);

  return websocket;
}

export async function postrequest(url, method, payload) {
  try {
    const response = await fetch(url, {
      method: method,
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken":
          document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
      },
      credentials: "include",
      body: JSON.stringify(payload),
    });

    console.log("response:", response);

    const result = await response.json();

    return {
      status: response.status,
      ok: response.ok,
      data: result,
    };
  } catch (error) {
    console.error("postrequest error:", error);
    return { status: 500, ok: false, data: { error: error.message } };
  }
}
