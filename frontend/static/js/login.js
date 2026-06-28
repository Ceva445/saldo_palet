// Login page logic.
if (token()) {
  location.href = "/dashboard";
}

async function submit() {
  const msg = document.getElementById("login-msg");
  msg.textContent = "";
  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: {
        username: document.getElementById("username").value,
        password: document.getElementById("password").value,
      },
    });
    localStorage.setItem("token", data.access_token);
    location.href = data.user.must_change_password ? "/change-password" : "/dashboard";
  } catch (e) {
    msg.textContent = e.message;
  }
}

document.getElementById("login-btn").onclick = submit;
document.getElementById("password").addEventListener("keydown", (e) => {
  if (e.key === "Enter") submit();
});
