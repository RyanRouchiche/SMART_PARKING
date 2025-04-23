


function openWebSocket() {

    const userStatusSocket = new WebSocket(`ws://${window.location.host}/ws/user-status/`);
    
    userStatusSocket.onopen = function () {
        console.log("WebSocket connection established.");
    };

    userStatusSocket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        console.log("WebSocket message received:", data);
        const statusElement = document.getElementById(`status-${data.user_id}`);
        if (statusElement) {
            statusElement.innerText = data.status;
        }
    };

    userStatusSocket.onerror = function (error) {
        console.error("WebSocket error:", error);
    };

    // userStatusSocket.onclose = function () {
    //     console.log("WebSocket connection closed.");
    //     userStatusSocket = null;
    // };
}

document.addEventListener("DOMContentLoaded", function () {
    openWebSocket();
});
