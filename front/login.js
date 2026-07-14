const $ = (id) => document.getElementById(id);

function baseUrl() {
  return $("baseUrl").value.replace(/\/$/, "");
}

function setStatus(message, isError = false) {
  $("loginStatus").textContent = message;
  $("loginStatus").style.color = isError ? "#d92d20" : "#667085";
}

async function login() {
  setStatus("\u6b63\u5728\u767b\u5f55...");
  const payload = {
    username: $("username").value.trim(),
    password: $("password").value.trim(),
  };

  try {
    const response = await fetch(`${baseUrl()}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",
      },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(`${response.status} ${data?.message || ""}`);
    saveSession(data);
  } catch (error) {
    const message = String(error?.message || "");
    setStatus(message.includes("401") ? "\u7528\u6237\u540d\u6216\u5bc6\u7801\u4e0d\u6b63\u786e" : "\u767b\u5f55\u5931\u8d25\uff0c\u8bf7\u68c0\u67e5\u540e\u7aef\u5730\u5740\u6216\u7f51\u7edc", true);
  }
}

function saveSession(data) {
  localStorage.setItem("visual_token", data.token);
  localStorage.setItem("visual_user", JSON.stringify(data.user));
  localStorage.setItem("visual_base_url", baseUrl());
  localStorage.removeItem("visual_mock_enabled");
  window.location.href = "./index.html";
}

$("loginBtn").addEventListener("click", () => login());
$("password").addEventListener("keydown", (event) => {
  if (event.key === "Enter") login();
});
