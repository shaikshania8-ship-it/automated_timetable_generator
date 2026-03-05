const API_URL = 'http://localhost:8000';

let currentSection = 'dashboard';
let currentTimetableType = 'class'; // class, faculty, room
let settings = { working_days: 5, periods_per_day: 6 };

// --- Navigation ---
function showSection(sectionId) {
    document.getElementById(currentSection).classList.add('hidden');
    document.getElementById(sectionId).classList.remove('hidden');
    
    // Update active nav item
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('onclick').includes(sectionId)) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    currentSection = sectionId;
    loadData();
}

// --- Data Loading ---
async function loadData() {
    try {
        const [facRes, subRes, classRes, roomRes, settingsRes, latestGenRes] = await Promise.all([
            fetch(`${API_URL}/faculty`),
            fetch(`${API_URL}/subjects`),
            fetch(`${API_URL}/classes`),
            fetch(`${API_URL}/rooms`),
            fetch(`${API_URL}/settings`),
            fetch(`${API_URL}/logs`)
        ]);

        const data = {
            faculty: await facRes.json(),
            subjects: await subRes.json(),
            classes: await classRes.json(),
            rooms: await roomRes.json(),
            settings: await settingsRes.json(),
            logs: await latestGenRes.json()
        };

        settings = data.settings;
        
        // Update Stats
        document.getElementById('stat-faculty').innerText = data.faculty.length;
        document.getElementById('stat-subjects').innerText = data.subjects.length;
        document.getElementById('stat-classes').innerText = data.classes.length;
        document.getElementById('stat-rooms').innerText = data.rooms.length;

        // Populate Tables
        renderTable('faculty-list-body', data.faculty, ['id', 'name', 'subject_expertise']);
        renderTable('subject-list-body', data.subjects, ['code', 'name', 'weekly_hours', 'type', 'class_id']);
        renderTable('class-list-body', data.classes, ['id', 'name', 'student_strength']);
        renderTable('room-list-body', data.rooms, ['id', 'name', 'capacity', 'type']);
        renderTable('logs-list-body', data.logs, ['timestamp', 'execution_time', 'soft_score', 'status']);

        // Populate Selects
        populateSelect('sub-class', data.classes, 'id', 'name');
        populateSelect('view-selector', data[currentTimetableType === 'class' ? 'classes' : (currentTimetableType === 'faculty' ? 'faculty' : 'rooms')], currentTimetableType === 'class' ? 'id' : 'id', 'name');

        // Update latest status
        if (data.logs.length > 0) {
            const latest = data.logs[0];
            const badge = document.getElementById('gen-status');
            badge.innerText = latest.status;
            badge.className = `badge badge-${latest.status.toLowerCase()}`;
            document.getElementById('gen-score').innerText = latest.soft_score.toFixed(2);
            document.getElementById('gen-time').innerText = latest.execution_time.toFixed(2) + 's';
            
            if (latest.status === 'Invalid') {
                document.getElementById('conflict-report').classList.remove('hidden');
                document.getElementById('conflict-list').innerHTML = `<li>${latest.fail_reason}</li>`;
            } else {
                document.getElementById('conflict-report').classList.add('hidden');
            }
        }

    } catch (err) {
        console.error('Error loading data:', err);
    }
}

function renderTable(id, data, fields) {
    const tbody = document.getElementById(id);
    if (!tbody) return;
    tbody.innerHTML = '';
    data.forEach(item => {
        const tr = document.createElement('tr');
        fields.forEach(field => {
            const td = document.createElement('td');
            if (field === 'timestamp') {
                td.innerText = new Date(item[field]).toLocaleString();
            } else if (field === 'execution_time') {
                td.innerText = item[field].toFixed(2) + 's';
            } else if (field === 'status') {
                td.innerHTML = `<span class="badge badge-${item[field].toLowerCase()}">${item[field]}</span>`;
            } else {
                td.innerText = item[field];
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}

function populateSelect(id, data, valField, textField) {
    const select = document.getElementById(id);
    if (!select) return;
    const currentVal = select.value;
    select.innerHTML = '<option value="">-- Choose --</option>';
    data.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item[valField];
        opt.innerText = item[textField];
        select.appendChild(opt);
    });
    if (currentVal) select.value = currentVal;
}

// --- Form Handlers ---
document.getElementById('faculty-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        id: document.getElementById('fac-id').value,
        name: document.getElementById('fac-name').value,
        subject_expertise: document.getElementById('fac-expert').value,
        availability: {} // Default: all available
    };
    // Initialize default availability (all 1s)
    for (let d = 0; d < settings.working_days; d++) {
        data.availability[d.toString()] = Array(settings.periods_per_day).fill(1);
    }
    
    const res = await fetch(`${API_URL}/add-faculty`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (res.ok) {
        e.target.reset();
        loadData();
    } else {
        alert('Error adding faculty');
    }
});

document.getElementById('subject-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        code: document.getElementById('sub-code').value,
        name: document.getElementById('sub-name').value,
        weekly_hours: parseInt(document.getElementById('sub-hours').value),
        type: document.getElementById('sub-type').value,
        class_id: document.getElementById('sub-class').value
    };
    const res = await fetch(`${API_URL}/add-subject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (res.ok) {
        e.target.reset();
        loadData();
    } else {
        alert('Error adding subject');
    }
});

document.getElementById('room-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        id: document.getElementById('room-id').value,
        name: document.getElementById('room-name').value,
        capacity: parseInt(document.getElementById('room-cap').value),
        type: document.getElementById('room-type').value
    };
    const res = await fetch(`${API_URL}/add-room`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (res.ok) {
        e.target.reset();
        loadData();
    }
});

document.getElementById('class-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        id: document.getElementById('class-id').value,
        name: document.getElementById('class-name').value,
        student_strength: parseInt(document.getElementById('class-strength').value)
    };
    const res = await fetch(`${API_URL}/add-class`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (res.ok) {
        e.target.reset();
        loadData();
    }
});

async function updateSettings() {
    const days = parseInt(document.getElementById('set-days').value);
    const periods = parseInt(document.getElementById('set-periods').value);
    const res = await fetch(`${API_URL}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ working_days: days, periods_per_day: periods })
    });
    if (res.ok) {
        alert('Settings saved!');
        loadData();
    }
}

// --- Timetable Logic ---
async function generateTimetable() {
    document.getElementById('loader').style.display = 'block';
    try {
        const res = await fetch(`${API_URL}/generate`, { method: 'POST' });
        const result = await res.json();
        await loadData();
        if (result.status === 'Valid') {
            alert('Timetable generated successfully!');
        } else {
            alert('Generation failed. Check the conflict report.');
        }
    } catch (err) {
        console.error(err);
    } finally {
        document.getElementById('loader').style.display = 'none';
    }
}

function switchTimetableTab(type) {
    currentTimetableType = type;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    const label = document.getElementById('selector-label');
    label.innerText = `Select ${type.charAt(0).toUpperCase() + type.slice(1)}`;
    
    // Refresh selector items
    loadData();
    renderTimetableGrid();
}

async function renderTimetableGrid() {
    const targetId = document.getElementById('view-selector').value;
    const container = document.getElementById('timetable-container');
    container.innerHTML = '';
    
    if (!targetId) return;
    
    const res = await fetch(`${API_URL}/timetable/${currentTimetableType}/${targetId}`);
    const entries = await res.json();
    
    // Create Headers
    const days = ['Slot', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    for (let day = 0; day <= settings.working_days; day++) {
        const h = document.createElement('div');
        h.className = 'slot-header';
        h.innerText = days[day];
        container.appendChild(h);
    }
    
    // Create Grid Body
    for (let p = 0; p < settings.periods_per_day; p++) {
        // Time label
        const timeLabel = document.createElement('div');
        timeLabel.className = 'slot';
        timeLabel.style.background = '#e2e8f0';
        timeLabel.style.fontWeight = 'bold';
        timeLabel.innerText = `P${p+1}`;
        container.appendChild(timeLabel);
        
        for (let d = 0; d < settings.working_days; d++) {
            const slot = document.createElement('div');
            slot.className = 'slot';
            
            const entry = entries.find(e => e.day === d && e.period === p);
            if (entry) {
                slot.classList.add('slot-assigned');
                slot.innerHTML = `
                    <div class="assigned-content">
                        <span class="assigned-subject">${entry.subject_code}</span>
                        <span class="assigned-info">${currentTimetableType === 'class' ? entry.faculty_id : entry.class_id}</span>
                        <span class="assigned-info">${entry.room_id}</span>
                    </div>
                `;
            } else {
                slot.innerText = '-';
                slot.style.textAlign = 'center';
                slot.style.lineHeight = '50px';
                slot.style.color = '#cbd5e1';
            }
            container.appendChild(slot);
        }
    }
    
    // Adjust grid columns
    container.style.gridTemplateColumns = `80px repeat(${settings.working_days}, 1fr)`;
}

// Download CSV Implementation
async function downloadCSV() {
    const targetId = document.getElementById('view-selector').value;
    if (!targetId) {
        alert('Please select a view first');
        return;
    }
    
    const res = await fetch(`${API_URL}/timetable/${currentTimetableType}/${targetId}`);
    const data = await res.json();
    
    let csv = 'Day,Period,Subject,Faculty,Class,Room\n';
    data.forEach(e => {
        csv += `${e.day},${e.period},${e.subject_code},${e.faculty_id},${e.class_id},${e.room_id}\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `timetable_${currentTimetableType}_${targetId}.csv`;
    a.click();
}

// Initial Load
window.onload = () => {
    loadData();
    // Default section is Dashboard, but ensure hidden states are correct
    showSection('dashboard');
};
