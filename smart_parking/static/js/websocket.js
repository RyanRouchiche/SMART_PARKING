export function initUserStatusWebSocket() {
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const userStatusSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/user-status/`);

    userStatusSocket.onopen = () => {
        console.log("WebSocket connection established.");
    };

    userStatusSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const statusElement = document.getElementById(`status-${data.user_id}`);
        if (statusElement) {
            statusElement.innerText = data.status;
        }
    };

    userStatusSocket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}
