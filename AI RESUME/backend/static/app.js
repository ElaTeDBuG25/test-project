async function postForm(url, formData) {
  const res = await fetch(url, { method: 'POST', body: formData });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

async function postJSON(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

function renderResults(payload) {
  const root = document.getElementById('results');
  const results = payload?.results || [];
  if (!results.length) {
    root.innerHTML = '<div class="muted">No candidates screened yet.</div>';
    return;
  }
  const rows = results.map(r => `
    <tr>
      <td>${r.id}</td>
      <td>${r.name || ''}</td>
      <td>${r.email || ''}</td>
      <td>${r.filename}</td>
      <td class="score">${(r.scores?.similarity ?? 0).toFixed(3)}</td>
      <td class="score">${(r.scores?.skill_overlap ?? 0).toFixed(3)}</td>
      <td class="score"><b>${(r.scores?.total ?? 0).toFixed(1)}</b></td>
      <td>${(r.skills || []).join(', ')}</td>
    </tr>
  `).join('');
  root.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Email</th>
          <th>File</th>
          <th>Similarity</th>
          <th>Skill Overlap</th>
          <th>Total</th>
          <th>Skills</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

// Job form
const jobForm = document.getElementById('job-form');
jobForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(jobForm);
  try {
    const res = await postForm('/api/job', fd);
    const skills = (res?.job?.skills || []).join(', ');
    document.getElementById('job-skills').textContent = skills ? `Detected job skills: ${skills}` : '';
  } catch (err) {
    alert('Failed to set job: ' + err);
  }
});

// Upload form
const uploadForm = document.getElementById('upload-form');
uploadForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(uploadForm);
  const filesInput = document.getElementById('files');
  if (!filesInput.files.length) return alert('Select at least one file');
  try {
    const res = await postForm('/api/upload', fd);
    document.getElementById('upload-status').textContent = `Uploaded ${res.count} file(s).`;
  } catch (err) {
    alert('Upload failed: ' + err);
  }
});

// Screen button
const screenBtn = document.getElementById('screen-btn');
screenBtn?.addEventListener('click', async () => {
  try {
    const res = await postJSON('/api/screen', {});
    renderResults(res);
  } catch (err) {
    alert('Screening failed: ' + err);
  }
});
