const serversBody = document.getElementById("servers-body");
const tasksBody = document.getElementById("tasks-body");

async function loadServers() {
  const res = await fetch("/api/servers");
  const data = await res.json();
  serversBody.innerHTML = "";
  data.forEach((s) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${s.hostname || ""}</td>
      <td>${s.ip || ""}</td>
      <td>${s.group || ""}</td>
      <td>${s.status || ""}</td>
      <td>${s.last_heartbeat || ""}</td>
      <td>${s.cpu_usage ?? ""}</td>
      <td>${s.memory_usage ?? ""}</td>
    `;
    serversBody.appendChild(tr);
  });
}

async function loadTasks() {
  const res = await fetch("/api/tasks");
  const data = await res.json();
  tasksBody.innerHTML = "";
  data.forEach((t) => {
    const tr = document.createElement("tr");
    const target = t.target_type === "all" ? "all" : `${t.target_type}:${t.target || ""}`;
    const btn = `<button data-task="${t.task_id}">查看</button>`;
    tr.innerHTML = `
      <td>${t.task_id}</td>
      <td>${target}</td>
      <td>${t.command}</td>
      <td>${t.status}</td>
      <td>${t.created_at}</td>
      <td>${btn}</td>
    `;
    tr.querySelector("button").addEventListener("click", async () => {
      const res2 = await fetch(`/api/tasks/${t.task_id}/results`);
      const results = await res2.json();
      alert(JSON.stringify(results, null, 2));
    });
    tasksBody.appendChild(tr);
  });
}

document.getElementById("add-server").addEventListener("click", async () => {
  const hostname = document.getElementById("hostname").value.trim();
  const ip = document.getElementById("ip").value.trim();
  const group = document.getElementById("group").value.trim();
  if (!hostname) {
    return;
  }
  await fetch("/api/servers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ hostname, ip: ip || null, group: group || null }),
  });
  document.getElementById("hostname").value = "";
  document.getElementById("ip").value = "";
  document.getElementById("group").value = "";
  await loadServers();
});

document.getElementById("send-command").addEventListener("click", async () => {
  const targetType = document.getElementById("target-type").value;
  const target = document.getElementById("target").value.trim();
  const command = document.getElementById("command").value.trim();
  const timeout = Number(document.getElementById("timeout").value) || 30;
  const user = document.getElementById("user").value.trim();
  if (!command) {
    return;
  }
  await fetch("/api/commands", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_type: targetType,
      target: target || null,
      command,
      timeout,
      user: user || null,
    }),
  });
  document.getElementById("command").value = "";
  await loadTasks();
});

loadServers();
loadTasks();
setInterval(loadServers, 5000);
setInterval(loadTasks, 5000);
