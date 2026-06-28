// Admin user-management page.
let currentUser = null;
let usersCache = [];
let rolesCache = [];
let editingUuid = null;

function esc(s) {
  return String(s).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function logout() {
  localStorage.removeItem("token");
  location.href = "/";
}

function roleOptions() {
  return rolesCache.map((r) => `<option value="${esc(r.name)}">${esc(r.name)}</option>`).join("");
}

async function loadRoles() {
  rolesCache = await api("/roles");
  document.getElementById("new-role").innerHTML = roleOptions();
  document.getElementById("edit-role").innerHTML = roleOptions();
}

async function loadUsers() {
  usersCache = await api("/users");
  document.getElementById("users-body").innerHTML = usersCache
    .map((u) => {
      const self = u.uuid === currentUser.uuid;
      return `<tr>
          <td>${esc(u.username)}</td>
          <td>${esc(u.role)}</td>
          <td>${u.is_active ? "aktywny" : "nieaktywny"}</td>
          <td>${u.must_change_password ? "wymagana" : "—"}</td>
          <td class="actions">
            <button class="edit" data-action="edit" data-uuid="${u.uuid}">Edytuj</button>
            ${self ? "" : `<button class="danger" data-action="delete" data-uuid="${u.uuid}">Usuń</button>`}
          </td>
        </tr>`;
    })
    .join("");
}

async function createUser() {
  const msg = document.getElementById("user-msg");
  msg.className = "msg";
  msg.textContent = "";

  const username = document.getElementById("new-username").value.trim();
  const password = document.getElementById("new-password").value;
  const role = document.getElementById("new-role").value;

  if (!username || !password) {
    msg.classList.add("error");
    msg.textContent = "Podaj nazwę użytkownika i hasło";
    return;
  }

  try {
    await api("/users", { method: "POST", body: { username, password, role } });
    document.getElementById("new-username").value = "";
    document.getElementById("new-password").value = "";
    msg.classList.add("ok");
    msg.textContent = "Użytkownik dodany";
    await loadUsers();
  } catch (e) {
    msg.classList.add("error");
    msg.textContent = e.message;
  }
}

function startEdit(uuid) {
  const user = usersCache.find((u) => u.uuid === uuid);
  if (!user) return;
  editingUuid = uuid;
  document.getElementById("edit-username").value = user.username;
  document.getElementById("edit-password").value = "";
  document.getElementById("edit-role").value = user.role;
  document.getElementById("edit-must-change").checked = !!user.must_change_password;
  document.getElementById("edit-msg").textContent = "";
  document.getElementById("edit-section").classList.remove("hidden");
  document.getElementById("edit-section").scrollIntoView({ behavior: "smooth" });
}

function cancelEdit() {
  editingUuid = null;
  document.getElementById("edit-section").classList.add("hidden");
}

async function saveEdit() {
  if (!editingUuid) return;
  const msg = document.getElementById("edit-msg");
  msg.className = "msg";
  msg.textContent = "";

  const body = {
    username: document.getElementById("edit-username").value.trim(),
    role: document.getElementById("edit-role").value,
    must_change_password: document.getElementById("edit-must-change").checked,
  };
  const password = document.getElementById("edit-password").value;
  if (password) body.password = password;

  try {
    await api(`/users/${editingUuid}`, { method: "PUT", body });
    cancelEdit();
    await loadUsers();
  } catch (e) {
    msg.classList.add("error");
    msg.textContent = e.message;
  }
}

async function deleteUser(uuid) {
  const user = usersCache.find((u) => u.uuid === uuid);
  if (!confirm(`Usunąć użytkownika "${user ? user.username : ""}"?`)) return;
  try {
    await api(`/users/${uuid}`, { method: "DELETE" });
    if (editingUuid === uuid) cancelEdit();
    await loadUsers();
  } catch (e) {
    document.getElementById("user-msg").className = "msg error";
    document.getElementById("user-msg").textContent = e.message;
  }
}

function wireTable() {
  document.getElementById("users-body").onclick = (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    if (btn.dataset.action === "edit") startEdit(btn.dataset.uuid);
    else if (btn.dataset.action === "delete") deleteUser(btn.dataset.uuid);
  };
}

async function boot() {
  if (!token()) {
    location.href = "/";
    return;
  }
  try {
    currentUser = await api("/auth/me");
    if (!currentUser.permissions.includes("users")) {
      location.href = "/dashboard";
      return;
    }
    document.getElementById("logout-btn").onclick = logout;
    document.getElementById("create-btn").onclick = createUser;
    document.getElementById("save-edit-btn").onclick = saveEdit;
    document.getElementById("cancel-edit-btn").onclick = cancelEdit;
    wireTable();
    await loadRoles();
    await loadUsers();
  } catch (e) {
    logout();
  }
}

boot();
