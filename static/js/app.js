// ==================== 全局变量 ====================
let students = [];
let selectedStudents = new Set();
let currentDay = '星期一';
let selectedPackage = null;

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', () => {
    initNav();
    loadStudents();
    loadPackages();
    loadEnrollments();
    loadSchedule();
    loadAttendance();
    loadStats();
    initSearch();
    document.getElementById('attendanceDate').value = new Date().toISOString().split('T')[0];
    const today = new Date().getDay();
    const dayMap = [7,1,2,3,4,5,6];
    const dayNames = ['','星期一','星期二','星期三','星期四','星期五','星期六','星期日'];
    document.getElementById('attendanceDay').value = dayNames[dayMap[today]] || '星期一';
    loadAttendanceSlots();
    loadAttendanceHistory();
});

// ==================== 导航 ====================
function initNav() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            item.classList.add('active');
            const tab = item.dataset.tab;
            document.getElementById('tab-' + tab).classList.add('active');
            if (tab === 'students') loadStudents();
            if (tab === 'enroll') { loadPackages(); loadEnrollments(); populateStudentSelect('enrollStudent'); }
            if (tab === 'schedule') loadSchedule();
            if (tab === 'attendance') { loadAttendanceSlots(); loadAttendanceHistory(); }
            if (tab === 'stats') loadStats();
        });
    });
}

// ==================== 搜索 ====================
function initSearch() {
    let timer;
    document.getElementById('globalSearch').addEventListener('input', e => {
        clearTimeout(timer);
        timer = setTimeout(() => loadStudents(e.target.value), 300);
    });
}

// ==================== 学员管理 ====================
async function loadStudents(search = '') {
    const status = document.getElementById('statusFilter').value;
    let url = '/api/students?';
    if (status) url += `status=${status}&`;
    if (search) url += `search=${encodeURIComponent(search)}`;
    const res = await fetch(url);
    students = await res.json();
    renderStudents();
}

function renderStudents() {
    const tbody = document.getElementById('studentsTable');
    tbody.innerHTML = students.map(s => `
        <tr>
            <td><input type="checkbox" ${selectedStudents.has(s.id)?'checked':''} onchange="toggleSelect('${s.id}')"></td>
            <td>${s.name}</td>
            <td>${s.phone || '-'}</td>
            <td>${s.level || '-'}</td>
            <td>${s.coach || '-'}</td>
            <td>${s.purchased_hours || 0}</td>
            <td>${s.bonus_hours || 0}</td>
            <td><strong>${s.remaining_hours || 0}</strong></td>
            <td><span class="badge badge-${s.status}">${s.status==='active'?'在读':s.status==='inactive'?'已结':'潜在'}</span></td>
            <td class="actions">
                <button class="btn btn-sm" onclick="editStudent('${s.id}')">编辑</button>
                <button class="btn btn-sm btn-danger" onclick="deleteStudent('${s.id}')">删除</button>
            </td>
        </tr>
    `).join('');
}

function toggleSelect(id) {
    if (selectedStudents.has(id)) selectedStudents.delete(id);
    else selectedStudents.add(id);
}

function toggleSelectAll() {
    const all = document.getElementById('selectAll').checked;
    selectedStudents.clear();
    if (all) students.forEach(s => selectedStudents.add(s.id));
    renderStudents();
}

async function deleteSelected() {
    if (selectedStudents.size === 0) return alert('请选择要删除的学员');
    if (!confirm(`确定删除 ${selectedStudents.size} 名学员？`)) return;
    await fetch('/api/students/batch', {
        method: 'DELETE',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ids: [...selectedStudents]})
    });
    selectedStudents.clear();
    loadStudents();
}

async function deleteStudent(id) {
    if (!confirm('确定删除该学员？')) return;
    await fetch('/api/students/batch', {
        method: 'DELETE',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ids: [id]})
    });
    loadStudents();
}

function showModal(id) {
    document.getElementById(id).classList.add('show');
    if (id === 'studentModal' && !document.getElementById('editStudentId').value) {
        document.getElementById('studentModalTitle').textContent = '添加学员';
        ['sName','sPhone','sCoach','sNote'].forEach(f => document.getElementById(f).value = '');
        document.getElementById('sPurchased').value = '0';
        document.getElementById('sBonus').value = '0';
    }
}

function hideModal(id) {
    document.getElementById(id).classList.remove('show');
    document.getElementById('editStudentId').value = '';
}

function editStudent(id) {
    const s = students.find(x => x.id === id);
    if (!s) return;
    document.getElementById('editStudentId').value = id;
    document.getElementById('studentModalTitle').textContent = '编辑学员';
    document.getElementById('sName').value = s.name;
    document.getElementById('sPhone').value = s.phone || '';
    document.getElementById('sLevel').value = s.level || '初级';
    document.getElementById('sCoach').value = s.coach || '';
    document.getElementById('sPurchased').value = s.purchased_hours || 0;
    document.getElementById('sBonus').value = s.bonus_hours || 0;
    document.getElementById('sNote').value = s.note || '';
    showModal('studentModal');
}

async function saveStudent() {
    const name = document.getElementById('sName').value.trim();
    if (!name) return alert('请输入姓名');
    const editId = document.getElementById('editStudentId').value;
    const body = {
        name,
        phone: document.getElementById('sPhone').value.trim(),
        level: document.getElementById('sLevel').value,
        coach: document.getElementById('sCoach').value.trim(),
        purchased_hours: parseFloat(document.getElementById('sPurchased').value) || 0,
        bonus_hours: parseFloat(document.getElementById('sBonus').value) || 0,
        note: document.getElementById('sNote').value.trim(),
        status: 'active'
    };
    if (editId) {
        body.remaining_hours = parseFloat(document.getElementById('sPurchased').value) + parseFloat(document.getElementById('sBonus').value);
        await fetch(`/api/students/${editId}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
    } else {
        body.remaining_hours = body.purchased_hours + body.bonus_hours;
        await fetch('/api/students', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
    }
    hideModal('studentModal');
    loadStudents();
}

async function importCSV() {
    const file = document.getElementById('csvFile').files[0];
    if (!file) return alert('请选择文件');
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/api/students/import-csv', { method: 'POST', body: fd });
    const data = await res.json();
    alert(`成功导入 ${data.imported} 条记录`);
    hideModal('importModal');
    loadStudents();
}

function exportStudents() {
    if (students.length === 0) return alert('无数据');
    let csv = '\uFEFF姓名,电话,等级,教练,购买课时,赠送课时,剩余课时,状态,备注\n';
    students.forEach(s => {
        csv += `${s.name},${s.phone},${s.level},${s.coach},${s.purchased_hours},${s.bonus_hours},${s.remaining_hours},${s.status},${s.note}\n`;
    });
    const blob = new Blob([csv], {type:'text/csv;charset=utf-8'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `学员导出_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
}

// ==================== 报课管理 ====================
async function loadPackages() {
    const res = await fetch('/api/packages');
    const packages = await res.json();
    const grid = document.getElementById('packagesGrid');
    grid.innerHTML = packages.map(p => `
        <div class="package-card" onclick="selectPackage('${p.id}', ${p.price_per_hour || p.price}, '${p.type}')">
            <h4>${p.name}</h4>
            <div class="price">${p.type === 'per_hour' ? '¥' + p.price_per_hour + '/节' : '¥' + p.price}</div>
            <div class="desc">${p.description}</div>
        </div>
    `).join('');
}

function selectPackage(id, price, type) {
    selectedPackage = { id, price, type };
    document.querySelectorAll('.package-card').forEach(c => c.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    document.getElementById('enrollPackage').value = id;
    onPackageChange();
}

function onPackageChange() {
    const pkgId = document.getElementById('enrollPackage').value;
    const hoursGroup = document.getElementById('hoursGroup');
    const priceDisplay = document.getElementById('priceDisplay');
    if (!pkgId) { priceDisplay.textContent = '请选择课程包'; return; }
    fetch('/api/packages').then(r=>r.json()).then(pkgs => {
        const pkg = pkgs.find(p => p.id === pkgId);
        if (!pkg) return;
        if (pkg.type === 'per_hour') {
            hoursGroup.style.display = 'block';
            calcPrice();
        } else {
            hoursGroup.style.display = 'none';
            priceDisplay.textContent = `${pkg.description}`;
        }
    });
}

function calcPrice() {
    const pkgId = document.getElementById('enrollPackage').value;
    const hours = parseInt(document.getElementById('enrollHours').value) || 0;
    fetch('/api/packages').then(r=>r.json()).then(pkgs => {
        const pkg = pkgs.find(p => p.id === pkgId);
        if (pkg && pkg.type === 'per_hour') {
            document.getElementById('priceDisplay').textContent = `总价: ¥${hours * pkg.price_per_hour}`;
        }
    });
}

async function doEnroll() {
    const studentId = document.getElementById('enrollStudent').value;
    const packageId = document.getElementById('enrollPackage').value;
    const hours = parseInt(document.getElementById('enrollHours').value) || 0;
    if (!studentId) return alert('请选择学员');
    if (!packageId) return alert('请选择课程包');
    const res = await fetch('/api/enroll', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ student_id: studentId, package_id: packageId, hours })
    });
    const data = await res.json();
    if (data.error) return alert(data.error);
    alert('报课成功！');
    loadEnrollments();
    loadStudents();
}

async function loadEnrollments() {
    const res = await fetch('/api/enrollments');
    const enrollments = await res.json();
    document.getElementById('enrollmentsTable').innerHTML = enrollments.map(e => `
        <tr><td>${e.student_name}</td><td>${e.package_name}</td><td>${e.hours}</td><td>¥${e.price}</td><td>${e.date}</td></tr>
    `).join('');
}

function populateStudentSelect(selectId) {
    fetch('/api/students').then(r=>r.json()).then(list => {
        const sel = document.getElementById(selectId);
        sel.innerHTML = '<option value="">-- 选择学员 --</option>' +
            list.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
    });
}

// ==================== 排课管理 ====================
async function loadSchedule() {
    const days = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日'];
    const tabsEl = document.getElementById('weekTabs');
    tabsEl.innerHTML = days.map(d => `<div class="week-tab ${d===currentDay?'active':''}" onclick="switchDay('${d}')">${d}</div>`).join('');

    const res = await fetch(`/api/schedules?day=${currentDay}`);
    const schedules = await res.json();
    const settingsRes = await fetch('/api/settings');
    const settings = await settingsRes.json();
    const timeSlots = settings.time_slots[currentDay] || [];
    const coaches = settings.coaches || [];
    const maxPerCoach = settings.max_students_per_coach || 6;

    const studentsRes = await fetch('/api/students');
    const allStudents = await studentsRes.json();
    const studentMap = {};
    allStudents.forEach(s => studentMap[s.id] = s);

    const grid = document.getElementById('scheduleGrid');
    grid.innerHTML = timeSlots.map(slot => {
        const slotSchedules = schedules.filter(s => s.time_slot === slot);
        const coachStudents = {};
        coaches.forEach(c => coachStudents[c] = []);
        slotSchedules.forEach(sc => {
            const student = studentMap[sc.student_id] || {};
            const coach = sc.coach || student.coach || coaches[0];
            if (!coachStudents[coach]) coachStudents[coach] = [];
            coachStudents[coach].push(student.name || '未知');
        });

        return `<div class="schedule-row">
            <div class="schedule-time">${slot}</div>
            ${coaches.map(c => {
                const list = coachStudents[c] || [];
                const count = list.length;
                const color = count < maxPerCoach ? 'var(--success)' : count === maxPerCoach ? 'var(--warning)' : 'var(--danger)';
                return `<div class="schedule-coach">
                    <h4><span>${c}</span><span class="count" style="color:${color}">${count}/${maxPerCoach}</span></h4>
                    ${list.length ? list.map(n => `<span class="student-tag">${n}</span>`).join('') : '<span style="color:#999;font-size:12px">(空)</span>'}
                </div>`;
            }).join('')}
        </div>`;
    }).join('');
}

function switchDay(day) {
    currentDay = day;
    loadSchedule();
}

async function importSchedule() {
    const file = document.getElementById('scheduleFile').files[0];
    if (!file) return alert('请选择文件');
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/api/schedules/import', { method: 'POST', body: fd });
    const data = await res.json();
    alert(`成功导入 ${data.imported} 条课表记录`);
    hideModal('importScheduleModal');
    loadSchedule();
}

async function clearSchedules() {
    if (!confirm('确定清空所有课表？')) return;
    await fetch('/api/schedules/clear', { method: 'POST' });
    loadSchedule();
}

// ==================== 消课点名 ====================
let attendanceStudents = [];
let selectedAttendance = new Set();

async function loadAttendanceSlots() {
    const day = document.getElementById('attendanceDay').value;
    const res = await fetch('/api/settings');
    const settings = await res.json();
    const slots = settings.time_slots[day] || [];
    const slotSel = document.getElementById('attendanceSlot');
    slotSel.innerHTML = slots.map(s => `<option>${s}</option>`).join('');
}

async function loadAttendanceStudents() {
    const day = document.getElementById('attendanceDay').value;
    const slot = document.getElementById('attendanceSlot').value;
    if (!slot) return alert('请选择时间段');
    const res = await fetch(`/api/schedules?day=${day}`);
    const schedules = await res.json();
    const matched = schedules.filter(s => s.time_slot === slot);
    const studentsRes = await fetch('/api/students');
    const allStudents = await studentsRes.json();
    const studentMap = {};
    allStudents.forEach(s => studentMap[s.id] = s);

    attendanceStudents = [];
    selectedAttendance.clear();
    matched.forEach(s => {
        const student = studentMap[s.student_id] || {};
        attendanceStudents.push({
            schedule_id: s.id,
            student_id: s.student_id,
            student_name: student.name || '未知',
            coach: s.coach || '',
            remaining_hours: student.remaining_hours || 0
        });
    });

    const tbody = document.getElementById('attendanceStudentsTable');
    tbody.innerHTML = attendanceStudents.map((a, i) => `
        <tr>
            <td><input type="checkbox" ${selectedAttendance.has(i)?'checked':''} onchange="toggleAttSelect(${i})"></td>
            <td>${a.student_name}</td>
            <td>${a.coach}</td>
            <td><strong>${a.remaining_hours}</strong></td>
            <td><span class="badge badge-active">待消课</span></td>
        </tr>
    `).join('');
    document.getElementById('attendanceCount').textContent = `共 ${attendanceStudents.length} 名学员`;
}

function toggleAttSelect(i) {
    if (selectedAttendance.has(i)) selectedAttendance.delete(i);
    else selectedAttendance.add(i);
}

function toggleAttSelectAll() {
    const all = document.getElementById('attSelectAll').checked;
    selectedAttendance.clear();
    if (all) attendanceStudents.forEach((_, i) => selectedAttendance.add(i));
    loadAttendanceStudents();
}

async function takeAttendance() {
    if (selectedAttendance.size === 0) return alert('请先选择要消课的学员');
    const date = document.getElementById('attendanceDate').value;
    const day = document.getElementById('attendanceDay').value;
    const slot = document.getElementById('attendanceSlot').value;
    const count = selectedAttendance.size;
    if (!confirm(`确定对 ${count} 名学员消课？`)) return;

    for (const i of selectedAttendance) {
        const a = attendanceStudents[i];
        await fetch('/api/attendance', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ student_id: a.student_id, hours_used: 1, date, schedule_id: a.schedule_id })
        });
    }
    alert(`已消课 ${count} 名学员`);
    selectedAttendance.clear();
    loadAttendanceStudents();
    loadAttendanceHistory();
}

async function loadAttendanceHistory() {
    const res = await fetch('/api/attendance');
    const attendances = await res.json();
    const studentsRes = await fetch('/api/students');
    const allStudents = await studentsRes.json();
    const studentMap = {};
    allStudents.forEach(s => studentMap[s.id] = s);
    document.getElementById('attendanceTable').innerHTML = attendances.map(a => {
        const s = studentMap[a.student_id] || {};
        return `<tr><td>${s.name || '未知'}</td><td>${a.hours_used}</td><td>${a.date}</td><td><span class="badge badge-active">已完成</span></td></tr>`;
    }).join('');
}

// 兼容旧函数名
async function loadAttendance() {
    loadAttendanceHistory();
}

// ==================== 统计中心 ====================
async function loadStats() {
    const res = await fetch('/api/stats');
    const stats = await res.json();
    document.getElementById('statsGrid').innerHTML = `
        <div class="stat-card"><div class="value">${stats.total_students}</div><div class="label">总学员数</div></div>
        <div class="stat-card"><div class="value">${stats.active_students}</div><div class="label">在读学员</div></div>
        <div class="stat-card"><div class="value">${stats.potential_students}</div><div class="label">潜在学员</div></div>
        <div class="stat-card"><div class="value">${stats.total_hours}</div><div class="label">总课时</div></div>
        <div class="stat-card"><div class="value">${stats.remaining_hours}</div><div class="label">剩余课时</div></div>
        <div class="stat-card"><div class="value">${stats.consumption_rate}%</div><div class="label">消耗率</div></div>
    `;
}
