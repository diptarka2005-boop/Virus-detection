const API = 'http://127.0.0.1:8000';
const $ = (id) => document.getElementById(id);
const formatTime = (value) => value ? new Date(value).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'}) : '--';

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, options);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}
function setStatus(status) {
  $('system-status').textContent = status;
  $('status-dot').style.background = status === 'HEALTHY' ? 'var(--teal)' : status === 'CRITICAL' ? 'var(--red)' : 'var(--orange)';
  $('status-caption').textContent = status === 'HEALTHY' ? 'All monitored signals are within their operating envelope.' : 'A fault condition is present or recovery is in progress.';
}
function renderFaults(rows) {
  $('fault-record-count').textContent = `${rows.length} records`;
  $('faults').innerHTML = rows.length ? rows.map(row => `<tr><td><b>${row.fault_type}</b><br><small>${formatTime(row.timestamp)}</small></td><td><span class="tag ${row.severity === 'CRITICAL' ? 'bad' : ''}">${row.severity}</span></td><td>${row.diagnosis || row.description}</td><td><span class="tag ${row.status !== 'RECOVERED' && row.status !== 'RESET' ? 'bad' : ''}">${row.status}</span></td></tr>`).join('') : '<tr><td colspan="4" class="empty">No events recorded yet.</td></tr>';
}
function renderRecoveries(rows) { $('recoveries').innerHTML = rows.length ? rows.map(row => `<tr><td>${row.action}<br><small>${formatTime(row.timestamp)}</small></td><td><span class="tag ${row.result !== 'SUCCESS' ? 'bad' : ''}">${row.result}</span></td><td>${row.attempts}</td></tr>`).join('') : '<tr><td colspan="3" class="empty">No recovery events yet.</td></tr>'; }
async function refresh() {
  try {
    const [status, faults, recoveries] = await Promise.all([request('/status'), request('/faults'), request('/recovery-history')]);
    setStatus(status.status); $('cpu').textContent = `${status.metrics.cpu_usage}%`; $('memory').textContent = `${status.metrics.memory_usage}%`; $('service').textContent = status.metrics.service_running ? 'RUNNING' : 'STOPPED'; $('health').textContent = status.health.healthy ? 'PASS' : 'FAIL'; $('fault-count').textContent = status.fault_count; $('recovery-count').textContent = status.recovery_count; $('failed-count').textContent = status.failed_recovery_count; $('last-sync').textContent = `Synced ${new Date().toLocaleTimeString()}`; renderFaults(faults); renderRecoveries(recoveries);
  } catch (error) { $('last-sync').textContent = 'Backend unavailable'; $('system-status').textContent = 'OFFLINE'; $('status-caption').textContent = error.message; }
}
document.querySelectorAll('button[data-action]').forEach(button => button.addEventListener('click', async () => { button.disabled = true; try { const result = await request(button.dataset.action, {method:'POST'}); $('action-message').textContent = result.message || `${button.textContent} completed.`; await refresh(); } catch (error) { $('action-message').textContent = error.message; } finally { button.disabled = false; } }));
refresh(); setInterval(refresh, 4000);
