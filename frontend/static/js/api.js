// Shared API helper used by every page.
function token() {
  return localStorage.getItem("token");
}

async function api(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token()) headers["Authorization"] = "Bearer " + token();

  const res = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    localStorage.removeItem("token");
    if (location.pathname !== "/") location.href = "/";
    throw new Error("Sesja wygasła");
  }

  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error((data && data.message) || "Błąd serwera");
  }
  return data;
}
