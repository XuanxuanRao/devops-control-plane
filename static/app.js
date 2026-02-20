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
      <td><button class="key-btn" data-hostname="${s.hostname}">编辑公钥</button></td>
    `;
    serversBody.appendChild(tr);
  });
}

// 使用事件委托处理公钥编辑按钮点击
serversBody.addEventListener('click', async (e) => {
  if (e.target.classList.contains('key-btn')) {
    const hostname = e.target.dataset.hostname;
    document.getElementById('edit-hostname').value = hostname;
    // 加载现有公钥
    try {
      const res = await fetch(`/api/client-keys/${hostname}`);
      if (res.ok) {
        const data = await res.json();
        document.getElementById('public-key-pem').value = data.public_key_pem || '';
      } else {
        document.getElementById('public-key-pem').value = '';
      }
    } catch (err) {
      document.getElementById('public-key-pem').value = '';
    }
    // 显示模态框
    document.getElementById('key-modal').style.display = 'block';
  }
});

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

// 模态框控制
const keyModal = document.getElementById('key-modal');
const closeBtn = document.querySelector('.close');
const saveBtn = document.getElementById('save-key');
const cancelBtn = document.getElementById('cancel-key');

// 关闭模态框
closeBtn.addEventListener('click', () => {
  keyModal.style.display = 'none';
});

cancelBtn.addEventListener('click', () => {
  keyModal.style.display = 'none';
});

// 点击模态框外部关闭
window.addEventListener('click', (e) => {
  if (e.target === keyModal) {
    keyModal.style.display = 'none';
  }
});

// 保存公钥
saveBtn.addEventListener('click', async () => {
  const hostname = document.getElementById('edit-hostname').value;
  const publicKeyPem = document.getElementById('public-key-pem').value.trim();
  
  if (!hostname) {
    alert('Hostname不能为空');
    return;
  }
  
  try {
    const res = await fetch(`/api/client-keys/${hostname}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ public_key_pem: publicKeyPem || '' }),
    });
    
    if (res.ok) {
      alert('公钥保存成功');
      keyModal.style.display = 'none';
    } else {
      const error = await res.json();
      alert(`保存失败: ${error.detail || '未知错误'}`);
    }
  } catch (err) {
    alert('保存失败: 网络错误');
  }
});
