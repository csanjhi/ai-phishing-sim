async function loadTemplates() {
  const rows = await (await fetch('/templates')).json();
  document.querySelector('#tmpl-table tbody').innerHTML = rows.map(t => `<tr>
    <td>${t.name}</td><td>${t.subject}</td><td>${t.department}</td>
    <td>${t.difficulty_level}</td><td>${t.model_used}</td>
    <td><code>${t.id}</code></td>
  </tr>`).join('');
}

async function loadCampaigns() {
  const rows = await (await fetch('/campaigns')).json();
  document.querySelector('#camp-table tbody').innerHTML = rows.map(c => `<tr>
    <td>${c.name} <br/><code>${c.id}</code></td>
    <td>${c.status}</td>
    <td>${c.approved_by || '-'}</td>
    <td>
      ${c.status === 'draft' ? `<button onclick="approve('${c.id}')">Approve</button>` : ''}
      ${c.status === 'approved' ? `<button onclick="launch('${c.id}')">Launch</button>` : ''}
    </td>
  </tr>`).join('');
}

async function approve(id) {
  const approved_by = prompt('Approving as (name/email):', 'security-lead@company.com');
  if (!approved_by) return;
  await fetch(`/campaigns/${id}/approve`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved_by }),
  });
  loadCampaigns();
}

async function launch(id) {
  await fetch(`/campaigns/${id}/launch`, { method: 'POST' });
  loadCampaigns();
}

document.querySelector('#tmpl-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = Object.fromEntries(fd.entries());
  body.push_to_gophish = fd.get('push_to_gophish') === 'on';
  const res = await fetch('/templates/generate', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  document.querySelector('#tmpl-result').textContent = JSON.stringify(await res.json(), null, 2);
  loadTemplates();
});

document.querySelector('#camp-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = Object.fromEntries(fd.entries());
  await fetch('/campaigns', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  e.target.reset();
  loadCampaigns();
});

document.querySelector('#event-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = Object.fromEntries(fd.entries());
  await fetch('/analytics/events', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  alert('Event recorded. Check the Analytics page.');
});

loadTemplates();
loadCampaigns();
