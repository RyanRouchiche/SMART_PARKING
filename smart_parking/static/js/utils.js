export async function sendrequest(url, method) {
  try {
    let response = await fetch(url, {
      method: method,
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (response.status === 401) {
      console.log("Token expired, refreshing...");
      const refreshRes = await fetch("/auth/token/refresh/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (refreshRes.ok) {
        console.log("Token refreshed successfully.");
        response = await fetch(url, {
          method: method,
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
        });
      } else {
        const res1 = await sendrequest("/auth/logout/", "POST");
        if (res1.status === 200) {
          window.location.href = "/";
        }
        return;
      }
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

export function initwebsocketconn(wsschema, path) {
  const websocket = new WebSocket(
    `${wsschema}://${window.location.host}/${path}`
  );

  console.log("WebSocket connection established:", websocket);

  return websocket;
}

export async function postrequest(url, method, payload) {
  async function makeRequest() {
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

    return response;
  }

  try {
    let response = await makeRequest();

    if (response.status === 401) {
      console.warn("Token expired. Trying to refresh...");

      const refreshResponse = await fetch("/auth/token/refresh/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (refreshResponse.ok) {
        console.log("Token refreshed. Retrying original request...");
        response = await makeRequest();
      } else {
        console.error("Token refresh failed.");
        if (window.location.pathname !== "/") {
          const res1 = await sendrequest("/auth/logout/", "POST");
          if (res1.status === 200) {
            window.location.href = "/";
          }
        }

        return {
          status: 401,
          ok: false,
          data: { error: "Token refresh failed" },
        };
      }
    }

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

export async function redirect(url) {
  console.log("Checking authentication...");
  const res = await fetch("/auth/check-auth/", {
    method: "GET",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "x-csrf-token":
        document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
    },
  });

  if (res.status === 401) {
    console.log("Token expired, refreshing...");
    const refreshRes = await fetch("/auth/token/refresh/", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "x-csrf-token":
          document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
      },
    });
    if (refreshRes.status === 200) {
      console.log("Token refreshed successfully. RRRR");
      window.location.href = url;
    } else {
      const res1 = await sendrequest("/auth/logout/", "POST");
      if (res1.status === 200) {
        window.location.href = "/";
      }
    }
  } else {
    window.location.href = url;
  }
}
export async function formPostRequest(url, payloadObj) {
  const formData = new URLSearchParams();
  for (const key in payloadObj) {
    formData.append(key, payloadObj[key]);
  }

  const csrfToken =
    document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";

  async function makeRequest() {
    return await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": csrfToken,
      },
      credentials: "include",
      body: formData.toString(),
    });
  }

  let response = await makeRequest();

  if (response.status === 401) {
    console.warn("Token expired. Refreshing before retry...");

    const refreshRes = await fetch("/auth/token/refresh/", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (refreshRes.ok) {
      console.log("Token refreshed. Retrying form POST...");
      response = await makeRequest();
    } else {
      console.error("Token refresh failed.");
      return { status: 401, ok: false, data: "Token refresh failed" };
    }
  }

  return {
    status: response.status,
    ok: response.ok,
    data: await response.text(),
  };
}
