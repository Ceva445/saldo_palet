// Forced / manual password change page.
function logout() {
  localStorage.removeItem("token");
  location.href = "/";
}

async function save() {
  const msg = document.getElementById("cp-msg");
  msg.className = "msg error";
  msg.textContent = "";

  const oldPwd = document.getElementById("old-password").value;
  const newPwd = document.getElementById("new-password").value;
  const newPwd2 = document.getElementById("new-password2").value;

  if (!oldPwd || !newPwd) {
    msg.textContent = "Podaj stare i nowe hasło";
    return;
  }
  if (newPwd !== newPwd2) {
    msg.textContent = "Nowe hasła nie są takie same";
    return;
  }

  try {
    await api("/auth/change-password", {
      method: "POST",
      body: { old_password: oldPwd, new_password: newPwd },
    });
    location.href = "/dashboard";
  } catch (e) {
    msg.textContent = e.message;
  }
}

async function boot() {
  if (!token()) {
    location.href = "/";
    return;
  }
  document.getElementById("save-btn").onclick = save;
  document.getElementById("new-password2").addEventListener("keydown", (e) => {
    if (e.key === "Enter") save();
  });
}

boot();
