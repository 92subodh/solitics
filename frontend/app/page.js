"use client";

import { useEffect, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const NAV = {
  ADMIN: [
    ["overview", "Overview", "HOME"],
    ["users", "User management", "USERS"],
    ["academic", "Academic assignments", "BOOK"],
    ["communication", "Communication", "CHAT"],
  ],
  FACULTY: [
    ["overview", "Dashboard", "HOME"],
    ["profile", "My profile", "PERSON"],
    ["teaching", "Teaching", "BOOK"],
    ["attendance", "Attendance", "CHECK"],
    ["exams", "Examination", "EXAM"],
    ["communication", "Communication", "CHAT"],
    ["leave", "Leave", "CAL"],
  ],
  STUDENT: [
    ["overview", "Dashboard", "HOME"],
    ["profile", "My profile", "PERSON"],
    ["academics", "Academics", "BOOK"],
    ["attendance", "Attendance", "CHECK"],
    ["exams", "Examination", "EXAM"],
    ["fees", "Fees", "CARD"],
    ["library", "Library", "BOOK"],
    ["communication", "Communication", "CHAT"],
    ["requests", "Requests", "FILE"],
    ["leave", "Leave", "CAL"],
    ["events", "Events & clubs", "STAR"],
  ],
  LIBRARIAN: [
    ["overview", "Dashboard", "HOME"],
    ["profile", "My profile", "PERSON"],
    ["books", "Books & copies", "BOOK"],
    ["circulation", "Circulation", "CHECK"],
    ["reservations", "Reservations", "FILE"],
    ["fines", "Fines", "CARD"],
    ["members", "Members", "USERS"],
    ["inventory", "Inventory", "BOX"],
    ["communication", "Library notices", "CHAT"],
    ["reports", "Reports", "CHART"],
  ],
};

async function request(path, token, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(options.headers || {}) },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || Object.values(data).flat().join(" ") || "Request failed");
  return data;
}

export default function Home() {
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState("overview");

  useEffect(() => {
    const saved = localStorage.getItem("erp_access_token");
    if (saved) request("/auth/me/", saved).then((data) => { setToken(saved); setUser(data); }).catch(() => localStorage.removeItem("erp_access_token")).finally(() => setLoading(false));
    else setLoading(false);
  }, []);

  async function login(credentials) {
    const data = await request("/auth/login/", "", { method: "POST", body: JSON.stringify(credentials) });
    const me = await request("/auth/me/", data.access);
    localStorage.setItem("erp_access_token", data.access);
    setToken(data.access);
    setUser(me);
  }

  function logout() {
    localStorage.removeItem("erp_access_token");
    setToken("");
    setUser(null);
    setActive("overview");
  }

  if (loading) return <div className="loader"><span className="mark">C</span><p>Preparing your workspace</p></div>;
  if (!user) return <Login onLogin={login} />;

  const role = user.role || "STUDENT";
  const navigation = NAV[role] || NAV.STUDENT;
  const current = navigation.find(([id]) => id === active) || navigation[0];
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="mark">C</span><span>Campus<em>ERP</em></span></div>
        <p className="side-caption">Connected campus operations</p>
        <div className="role-chip"><span className="status-dot" />{role.toLowerCase()} workspace</div>
        <nav>{navigation.map(([id, label, icon]) => <button className={active === id ? "nav-item active" : "nav-item"} key={id} onClick={() => setActive(id)}><Icon name={icon} /><span>{label}</span></button>)}</nav>
        <div className="sidebar-foot"><div className="avatar">{initials(user)}</div><div><strong>{user.first_name || user.username}</strong><small>{user.email || role}</small></div><button className="logout" title="Sign out" onClick={logout}>↗</button></div>
      </aside>
      <main className="main-content">
        <header className="topbar"><div><span className="eyebrow">{role} PORTAL</span><h1>{current[1]}</h1></div><div className="top-actions"><span className="date-label">{new Intl.DateTimeFormat("en", { weekday: "long", month: "short", day: "numeric" }).format(new Date())}</span><button className="icon-button" title="Notifications">◌</button></div></header>
        <div className="content-wrap"><View role={role} id={current[0]} token={token} user={user} /></div>
      </main>
    </div>
  );
}

function Login({ onLogin }) {
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) { event.preventDefault(); setBusy(true); setError(""); try { await onLogin(credentials); } catch (err) { setError(err.message); } finally { setBusy(false); } }
  return <main className="login-screen"><section className="login-card"><div className="brand login-brand"><span className="mark">C</span><span>Campus<em>ERP</em></span></div><span className="eyebrow">COLLEGE OPERATIONS PORTAL</span><h1>Everything your campus needs, in one place.</h1><p className="muted lead">Sign in to access the workspace assigned to your role.</p><form onSubmit={submit} className="login-form"><Field label="Username"><input autoComplete="username" required value={credentials.username} onChange={(e) => setCredentials({ ...credentials, username: e.target.value })} /></Field><Field label="Password"><input type="password" autoComplete="current-password" required value={credentials.password} onChange={(e) => setCredentials({ ...credentials, password: e.target.value })} /></Field>{error && <div className="error-message">{error}</div>}<button className="primary-button" disabled={busy}>{busy ? "Signing in..." : "Sign in to CampusERP"}</button></form><p className="login-note">Need access? Contact your institution administrator.</p></section><section className="login-aside"><div className="aside-grid" /><div className="aside-copy"><span className="eyebrow light">ONE CONNECTED CAMPUS</span><h2>Make every academic day feel more considered.</h2><p>Secure, role-based tools for the people who keep learning moving.</p></div><div className="aside-footer"><span>ADMIN</span><span>FACULTY</span><span>STUDENT</span></div></section></main>;
}

function View({ role, id, token, user }) {
  if (role === "ADMIN") { if (id === "users") return <AdminUsers token={token} />; if (id === "academic") return <><DepartmentBuilder token={token} /><ProgramsPanel token={token} /><AdminAcademic token={token} /></>; if (id === "communication") return <AdminCommunication token={token} />; return <AdminOverview token={token} user={user} />; }
  if (role === "FACULTY") return <FacultyView id={id} token={token} />;
  if (role === "LIBRARIAN") return <LibrarianView id={id} token={token} />;
  return <StudentView id={id} token={token} />;
}

function AdminOverview({ token, user }) {
  return <DashboardFrame eyebrow="ADMINISTRATION" title={`Good morning, ${user.first_name || user.username}.`} description="Keep the people and access layer of your ERP precise and current."><Stats items={[{ label: "Active users", path: "/admin/users/?status=active", key: "count", tone: "blue" }, { label: "Administrators", path: "/admin/users/?role=ADMIN", key: "count", tone: "yellow" }, { label: "Faculty", path: "/admin/users/?role=FACULTY", key: "count", tone: "green" }]} token={token} /><div className="split-grid"><InfoPanel title="Admin focus" kicker="PHASE 1"><p className="panel-copy">User management is the control room for this phase. Create accounts, assign multiple roles, and keep access current without touching academic records.</p><div className="mini-list"><span><b>01</b> Create and edit accounts</span><span><b>02</b> Assign role combinations</span><span><b>03</b> Deactivate without deleting history</span></div></InfoPanel><InfoPanel title="Quick action" kicker="USER MANAGEMENT"><button className="action-link" onClick={() => window.location.hash = "users"}>Open user management <span>↗</span></button><p className="muted">Role changes and credential resets are audited automatically.</p></InfoPanel></div></DashboardFrame>;
}

function AdminUsers({ token }) {
  const [data, setData] = useState({ count: 0, results: [] });
  const [query, setQuery] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  useEffect(() => { request(`/admin/users/${query ? `?search=${encodeURIComponent(query)}` : ""}`, token).then(setData).catch((err) => setError(err.message)); }, [token, query, refresh]);
  async function toggle(user) { try { await request(`/admin/users/${user.user_id}/status/`, token, { method: "PATCH", body: JSON.stringify({ is_active: !user.is_active }) }); setRefresh((n) => n + 1); } catch (err) { setError(err.message); } }
  async function reset(user) { const password = window.prompt(`New password for ${user.username}`); if (!password) return; try { await request(`/admin/users/${user.user_id}/reset-password/`, token, { method: "POST", body: JSON.stringify({ new_password: password }) }); } catch (err) { setError(err.message); } }
  async function remove(user) {
    if (!window.confirm(`Are you sure you want to completely delete ${user.first_name || user.username}? This cannot be undone.`)) return;
    try {
      await request(`/admin/users/${user.user_id}/`, token, { method: "DELETE" });
      setRefresh((n) => n + 1);
    } catch (err) { setError(err.message); }
  }
  return <DashboardFrame eyebrow="ACCESS CONTROL" title="User management" description="Create accounts, manage roles, and keep access aligned with the institution."><div className="toolbar"><div className="search-box"><span>⌕</span><input placeholder="Search by name, username, or email" value={query} onChange={(e) => setQuery(e.target.value)} /></div><button className="primary-button compact" onClick={() => setShowForm(true)}>＋ Create user</button></div>{error && <div className="error-message">{error}</div>}{showForm && <CreateUser token={token} close={() => setShowForm(false)} done={() => { setShowForm(false); setRefresh((n) => n + 1); }} /> }<div className="table-card"><div className="table-heading"><div><span className="eyebrow">DIRECTORY</span><h2>All users</h2></div><span className="count-pill">{data.count} accounts</span></div><table><thead><tr><th>Person</th><th>ID / Roll No</th><th>Roles</th><th>Status</th><th>Actions</th></tr></thead><tbody>{data.results.map((item) => <tr key={item.user_id}><td><div className="person-cell"><span className="avatar small">{initials(item)}</span><span><strong>{item.first_name} {item.last_name}</strong><small>{item.email}</small></span></div></td><td className="mono">{item.identifier || item.username}</td><td><div className="role-list">{(item.roles || []).map((role) => <span key={role} className="tag">{role}</span>)}</div></td><td><span className={item.is_active ? "status active" : "status inactive"}><i />{item.is_active ? "Active" : "Inactive"}</span></td><td><div className="row-actions"><button onClick={() => toggle(item)}>{item.is_active ? "Deactivate" : "Activate"}</button><button onClick={() => reset(item)}>Reset password</button>{!(item.roles || []).includes("ADMIN") && <button style={{ color: "#bf6871" }} onClick={() => remove(item)}>Delete</button>}</div></td></tr>)}</tbody></table>{!data.results.length && <Empty title="No users found" text="Try a different search or create the first account." />}</div></DashboardFrame>;
}

function CreateUser({ token, close, done }) {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", phone: "", username: "", password: "", roles: ["STUDENT"], admission_number: "", roll_number: "", employee_code: "", parent_code: "" });
  const [error, setError] = useState("");
  function update(key, value) { setForm({ ...form, [key]: value }); }
  
  async function submit(event) { 
    event.preventDefault(); 
    try { 
      const profile_data = {};
      let username = "";
      if (form.roles.includes("STUDENT")) { 
        profile_data.roll_number = form.roll_number; 
        username = form.roll_number.toString();
      }
      else if (form.roles.includes("FACULTY") || form.roles.includes("LIBRARIAN") || form.roles.includes("ADMIN")) { 
        profile_data.employee_code = form.employee_code; 
        username = form.employee_code.toString();
      }
      else if (form.roles.includes("PARENT")) { 
        profile_data.parent_code = form.parent_code; 
        username = form.parent_code.toString();
      }

      await request("/admin/users/", token, { method: "POST", body: JSON.stringify({ ...form, username, profile_data }) }); 
      done(); 
    } catch (err) { setError(err.message); } 
  }

  const roleOpts = ["STUDENT", "FACULTY", "ADMIN", "LIBRARIAN", "PARENT"];

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="modal-head">
          <div><span className="eyebrow">NEW ACCOUNT</span><h2>Create a user</h2></div>
          <button className="close-button" onClick={close}>×</button>
        </div>
        
        {step === 1 ? (
          <form className="form-grid" onSubmit={(e) => { e.preventDefault(); setStep(2); }}>
            <div className="field full">
              <span className="field-label">Select user role</span>
              <p className="muted" style={{ marginBottom: 16, fontSize: "0.85rem" }}>The user's role will determine the details needed for registration.</p>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: 8 }}>
                {roleOpts.map((role) => (
                  <button type="button" key={role} className={form.roles.includes(role) ? "primary-button" : "secondary-button"} onClick={() => update("roles", [role])}>{role}</button>
                ))}
              </div>
            </div>
            <div className="modal-actions full" style={{ marginTop: 24 }}>
              <button type="button" className="secondary-button" onClick={close}>Cancel</button>
              <button className="primary-button">Continue</button>
            </div>
          </form>
        ) : (
          <form className="form-grid" onSubmit={submit}>
            <Field label="First name"><input required value={form.first_name} onChange={(e) => update("first_name", e.target.value)} /></Field>
            <Field label="Last name"><input required value={form.last_name} onChange={(e) => update("last_name", e.target.value)} /></Field>
            <Field label="Email"><input type="email" required value={form.email} onChange={(e) => update("email", e.target.value)} /></Field>
            <Field label="Phone (Optional)"><input value={form.phone} onChange={(e) => update("phone", e.target.value)} /></Field>
            <Field label="Temporary password"><input type="password" minLength="8" required value={form.password} onChange={(e) => update("password", e.target.value)} /></Field>

            {form.roles.includes("STUDENT") && (
              <>
                <Field label="Roll number"><input type="number" required value={form.roll_number} onChange={(e) => update("roll_number", e.target.value)} /></Field>
              </>
            )}
            {(form.roles.includes("FACULTY") || form.roles.includes("LIBRARIAN") || form.roles.includes("ADMIN")) && (
              <>
                <Field label="Employee code"><input type="number" required value={form.employee_code} onChange={(e) => update("employee_code", e.target.value)} /></Field>
              </>
            )}
            {form.roles.includes("PARENT") && (
              <>
                <Field label="Parent code (Optional)"><input value={form.parent_code} onChange={(e) => update("parent_code", e.target.value)} /></Field>
              </>
            )}
            
            {error && <div className="error-message full">{error}</div>}
            <div className="modal-actions full" style={{ marginTop: 16 }}>
              <button type="button" className="secondary-button" onClick={() => setStep(1)}>Back</button>
              <button className="primary-button">Create account</button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function AdminAcademic({ token }) {
  const [options, setOptions] = useState({ students: [], faculty: [], programs: [], semesters: [], academic_years: [], sections: [], subjects: [] });
  const [assignments, setAssignments] = useState([]);
  const [studentForm, setStudentForm] = useState({ admission_number: "", program: "", semester: "" });
  const [studentLookup, setStudentLookup] = useState(null);
  const [facultyForm, setFacultyForm] = useState({ employee_code: "", subject: "" });
  const [facultyLookup, setFacultyLookup] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    request("/admin/academic-options/", token).then(setOptions).catch((err) => setError(err.message));
    request("/admin/faculty-assignments/", token).then((data) => setAssignments(data.results || data)).catch(() => {});
  }, [token]);

  const studentSemesters = options.semesters.filter((s) => String(s.program_id) === String(studentForm.program));

  // Look up student by admission number or roll number
  async function lookupStudent() {
    if (!studentForm.admission_number.trim()) return;
    setStudentLookup(null); setError("");
    const searchVal = studentForm.admission_number.trim();
    const match = options.students.find((s) => s.admission_number === searchVal || String(s.current_roll_number) === searchVal);
    if (match) {
      setStudentLookup(match);
    } else {
      setError("No student found with Roll No / Admission No: " + searchVal);
    }
  }

  // Look up faculty by employee code
  async function lookupFaculty() {
    if (!facultyForm.employee_code.trim()) return;
    setFacultyLookup(null); setError("");
    const searchVal = facultyForm.employee_code.trim();
    const match = options.faculty.find((f) => String(f.employee__employee_code) === searchVal);
    if (match) {
      setFacultyLookup(match);
    } else {
      setError("No faculty found with employee code: " + searchVal);
    }
  }

  async function placeStudent(event) {
    event.preventDefault();
    setMessage(""); setError("");
    if (!studentLookup) { setError("Look up a student first."); return; }
    try {
      // Find a section matching program + semester (use first available, picking latest academic year)
      const matchingSections = options.sections.filter((s) =>
        String(s.program_id) === String(studentForm.program) &&
        String(s.semester_id) === String(studentForm.semester)
      ).sort((a, b) => b.academic_year_id - a.academic_year_id);
      
      const sectionId = matchingSections.length > 0 ? matchingSections[0].section_id : null;
      const academicYearId = matchingSections.length > 0 ? matchingSections[0].academic_year_id : null;

      await request(`/admin/students/${studentLookup.student_id}/academic/`, token, {
        method: "PATCH",
        body: JSON.stringify({
          program: Number(studentForm.program),
          semester: Number(studentForm.semester),
          section: sectionId ? Number(sectionId) : undefined,
          academic_year: academicYearId ? Number(academicYearId) : undefined,
        })
      });
      setMessage("Student placement saved successfully.");
      setStudentLookup(null);
      setStudentForm({ admission_number: "", program: "", semester: "" });
    } catch (err) { setError(err.message); }
  }

  async function assignFaculty(event) {
    event.preventDefault();
    setMessage(""); setError("");
    if (!facultyLookup) { setError("Look up a faculty member first."); return; }

    // Find the subject and its program/semester context
    const subject = options.subjects.find((s) => String(s.id) === String(facultyForm.subject));
    if (!subject) { setError("Please select a course."); return; }

    try {
      await request("/admin/faculty-assignments/", token, {
        method: "POST",
        body: JSON.stringify({
          faculty: Number(facultyLookup.id),
          subject: Number(facultyForm.subject),
        })
      });
      const updated = await request("/admin/faculty-assignments/", token);
      setAssignments(updated.results || updated);
      setMessage("Faculty assignment saved.");
      setFacultyLookup(null);
      setFacultyForm({ employee_code: "", subject: "" });
    } catch (err) { setError(err.message); }
  }

  return (
    <DashboardFrame eyebrow="ACADEMIC ADMINISTRATION" title="Academic assignments" description="Assign students to programs and faculty to courses.">
      {error && <div className="error-message page-message">{error}</div>}
      {message && <p className="form-message page-message">{message}</p>}
      <div className="split-grid">
        <form className="panel compact-form" onSubmit={placeStudent}>
          <span className="eyebrow">STUDENT PLACEMENT</span>
          <h2>Assign student to program</h2>
          <Field label="Roll No / Admission No">
            <div className="lookup-row">
              <input required placeholder="e.g. ADM2024001" value={studentForm.admission_number} onChange={(e) => { setStudentForm({ ...studentForm, admission_number: e.target.value }); setStudentLookup(null); }} />
              <button type="button" className="secondary-button" onClick={lookupStudent}>Look up</button>
            </div>
          </Field>
          {studentLookup && (
            <div className="lookup-result">
              <span className="lookup-name">{studentLookup.user__first_name} {studentLookup.user__last_name}</span>
              <span className="lookup-id">ID: {studentLookup.student_id}</span>
            </div>
          )}
          <Field label="Program">
            <select required value={studentForm.program} onChange={(e) => setStudentForm({ ...studentForm, program: e.target.value, semester: "" })}>
              <option value="">Choose program</option>
              {options.programs.map((p) => <option key={p.id} value={p.id}>{p.program_code} &middot; {p.program_name}</option>)}
            </select>
          </Field>
          <Field label="Semester">
            <select required value={studentForm.semester} onChange={(e) => setStudentForm({ ...studentForm, semester: e.target.value })}>
              <option value="">Choose semester</option>
              {studentSemesters.map((s) => <option key={s.id} value={s.id}>Semester {s.semester_number}</option>)}
            </select>
          </Field>
          <button className="primary-button compact" disabled={!studentLookup}>Assign program</button>
        </form>

        <form className="panel compact-form" onSubmit={assignFaculty}>
          <span className="eyebrow">TEACHING ASSIGNMENT</span>
          <h2>Assign faculty to course</h2>
          <Field label="Faculty employee code">
            <div className="lookup-row">
              <input required placeholder="e.g. EMP001" value={facultyForm.employee_code} onChange={(e) => { setFacultyForm({ ...facultyForm, employee_code: e.target.value }); setFacultyLookup(null); }} />
              <button type="button" className="secondary-button" onClick={lookupFaculty}>Look up</button>
            </div>
          </Field>
          {facultyLookup && (
            <div className="lookup-result">
              <span className="lookup-name">{facultyLookup.employee__user__first_name} {facultyLookup.employee__user__last_name}</span>
              <span className="lookup-id">Code: {facultyLookup.employee__employee_code}</span>
            </div>
          )}
          <Field label="Course (subject)">
            <select required value={facultyForm.subject} onChange={(e) => setFacultyForm({ ...facultyForm, subject: e.target.value })}>
              <option value="">Choose course</option>
              {options.subjects.map((s) => <option key={s.id} value={s.id}>{s.subject_code} &middot; {s.subject_name}</option>)}
            </select>
          </Field>
          <button className="primary-button compact" disabled={!facultyLookup}>Assign course</button>
        </form>
      </div>
      <InfoPanel title="Current faculty assignments" kicker="TEACHING MAP">
        <DataTable columns={["Faculty", "Subject", "Section", "Semester", "Year"]} rows={assignments.map((a) => [a.faculty_name || a.faculty, a.subject_code || a.subject, a.section_code || a.section, a.semester_number || a.semester, a.academic_year_code || a.academic_year])} />
      </InfoPanel>
    </DashboardFrame>
  );
}

function AdminCommunication({ token }) {
  const [notices, setNotices] = useState([]);
  const [posts, setPosts] = useState([]);
  const [message, setMessage] = useState("");
  
  useEffect(() => {
    Promise.all([request("/notices/", token), request("/posts/", token)]).then(([a, b]) => {
      setNotices(a.results || a);
      setPosts(b.results || b);
    });
  }, [token]);

  async function submitNotice(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await request("/notices/", token, { method: "POST", body: JSON.stringify(Object.fromEntries(form.entries())) });
      const data = await request("/notices/", token);
      setNotices(data.results || data);
      setMessage("Notice broadcasted successfully.");
      event.currentTarget.reset();
    } catch(err) { setMessage(err.message); }
  }

  async function submitPost(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await request("/posts/", token, { method: "POST", body: JSON.stringify(Object.fromEntries(form.entries())) });
      const data = await request("/posts/", token);
      setPosts(data.results || data);
      setMessage("Global post published successfully.");
      event.currentTarget.reset();
    } catch(err) { setMessage(err.message); }
  }

  return <DashboardFrame eyebrow="COMMUNICATION" title="Campus updates" description="Broadcast notices or publish general posts for the entire campus.">{message && <div className="form-message page-message">{message}</div>}<div className="split-grid"><form className="panel compact-form" onSubmit={submitNotice}><span className="eyebrow">NEW NOTICE</span><h2>Broadcast a notice</h2><Field label="Title"><input name="title" required /></Field><Field label="Audience"><select name="audience" required defaultValue="ALL"><option value="ALL">All campus</option><option value="STUDENT">Students only</option><option value="FACULTY">Faculty only</option></select></Field><Field label="Body"><textarea name="body" required rows="4" /></Field><button className="primary-button compact">Broadcast notice</button></form><form className="panel compact-form" onSubmit={submitPost}><span className="eyebrow">NEW POST</span><h2>Publish a global post</h2><Field label="Title"><input name="title" required /></Field><Field label="Visibility"><select name="visibility" required defaultValue="ALL"><option value="ALL">Everyone</option></select></Field><Field label="Content"><textarea name="content" required rows="4" /></Field><button className="primary-button compact">Publish post</button></form></div><div className="split-grid"><InfoPanel title="Recent notices" kicker="BROADCASTS"><DataTable columns={["Title", "Audience", "Published"]} rows={notices.map((item) => [item.title, item.audience, new Date(item.published_at).toLocaleDateString()])} /></InfoPanel><InfoPanel title="Recent posts" kicker="FEED"><DataTable columns={["Title", "Visibility", "Published"]} rows={posts.map((item) => [item.title, item.visibility, new Date(item.created_at).toLocaleDateString()])} /></InfoPanel></div></DashboardFrame>;
}

function DepartmentBuilder({ token }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ department_code: "", department_name: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [departments, setDepartments] = useState([]);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    request("/admin/departments/", token)
      .then((data) => setDepartments(data.results || data))
      .catch(() => {});
  }, [token, refresh]);

  async function submit(event) {
    event.preventDefault();
    setMessage(""); setError("");
    try {
      const data = await request("/admin/departments/", token, { method: "POST", body: JSON.stringify(form) });
      setMessage(`${data.department_name} created.`);
      setForm({ department_code: "", department_name: "" });
      setOpen(false);
      setRefresh((n) => n + 1);
      window.dispatchEvent(new Event("academic-options-updated"));
    } catch (err) { setError(err.message); }
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="eyebrow">ACADEMIC HIERARCHY · LEVEL 1</span>
          <h2>Departments</h2>
        </div>
        <button className="primary-button compact" onClick={() => setOpen(!open)}>{open ? "Cancel" : "＋ Add department"}</button>
      </div>
      {open && (
        <form className="inline-form" onSubmit={submit} style={{ marginBottom: 16 }}>
          <Field label="Department code"><input required placeholder="CSE" value={form.department_code} onChange={(e) => setForm({ ...form, department_code: e.target.value })} /></Field>
          <Field label="Department name"><input required placeholder="Computer Science" value={form.department_name} onChange={(e) => setForm({ ...form, department_name: e.target.value })} /></Field>
          <button className="primary-button compact" style={{ alignSelf: "flex-end" }}>Create</button>
        </form>
      )}
      {error && <div className="error-message" style={{ marginBottom: 12 }}>{error}</div>}
      {message && <p className="form-message" style={{ marginBottom: 12 }}>{message}</p>}
      {departments.length === 0 && !open && <Empty title="No departments yet" text="Add the first department to get started." />}
      {departments.length > 0 && (
        <div className="dept-list">
          {departments.map((dept) => (
            <div className="dept-row" key={dept.id}>
              <span className="dept-code">{dept.department_code}</span>
              <span className="dept-name">{dept.department_name}</span>
              <span className="tag">{dept.program_count ?? 0} programs</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function ProgramsPanel({ token }) {
  const [departments, setDepartments] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const blankCourse = () => ({ code: "", name: "", credits: "3" });
  const blankForm = { program_code: "", program_name: "", department: "", degree_type: "B.Tech", duration_years: 4, semester_count: 8 };
  const [form, setForm] = useState(blankForm);
  const [semesterCourses, setSemesterCourses] = useState(() => Array.from({ length: 8 }, () => []));
  const [editForm, setEditForm] = useState({});
  const [removedSubjects, setRemovedSubjects] = useState([]);

  async function loadAll() {
    // Load departments (via academic-options) independently from programs
    // so a 405 on /admin/programs/ doesn't block the department dropdown
    try {
      const opts = await request("/admin/academic-options/", token);
      setDepartments(opts.departments || []);
    } catch (err) { setMessage(err.message); }

    try {
      const progs = await request("/admin/programs/", token);
      setPrograms(progs.results || progs);
    } catch (_) { /* programs endpoint may not support GET yet */ }
  }

  useEffect(() => {
    loadAll();
    const handler = () => loadAll();
    window.addEventListener("academic-options-updated", handler);
    window.addEventListener("programs-updated", handler);
    return () => {
      window.removeEventListener("academic-options-updated", handler);
      window.removeEventListener("programs-updated", handler);
    };
  }, [token, refresh]);

  function addCourse(semIndex) {
    setSemesterCourses((prev) => { const next = [...prev]; next[semIndex] = [...(next[semIndex] || []), blankCourse()]; return next; });
  }
  function removeCourse(semIndex, courseIndex) {
    setSemesterCourses((prev) => { 
      const next = [...prev]; 
      const course = next[semIndex][courseIndex];
      if (course && course.existing_id) {
        setRemovedSubjects((r) => [...r, course.existing_id]);
      }
      next[semIndex] = next[semIndex].filter((_, i) => i !== courseIndex); 
      return next; 
    });
  }
  function updateCourse(semIndex, courseIndex, field, value) {
    setSemesterCourses((prev) => { const next = prev.map((s) => [...s]); next[semIndex][courseIndex] = { ...next[semIndex][courseIndex], [field]: value }; return next; });
  }
  function handleSemCount(count) {
    setForm((f) => ({ ...f, semester_count: Number(count) }));
    setSemesterCourses((prev) => Array.from({ length: Number(count) }, (_, i) => prev[i] || []));
  }

  async function createProgram(event) {
    event.preventDefault();
    setMessage(""); setError("");
    try {
      const semesters = Array.from({ length: Number(form.semester_count) }, (_, i) => ({
        semester_number: i + 1,
        courses: (semesterCourses[i] || []).filter((c) => c.code && c.name).map((c) => ({ code: c.code.trim(), name: c.name.trim(), credits: Number(c.credits) || 3, subject_type: "CORE", is_core: true }))
      }));
      const result = await request("/admin/programs/", token, { method: "POST", body: JSON.stringify({ ...form, department: Number(form.department), duration_years: Number(form.duration_years), semesters }) });
      setMessage(`✓ ${result.program_name} created with ${result.course_count} courses.`);
      setShowCreate(false);
      setForm(blankForm);
      setSemesterCourses(Array.from({ length: 8 }, () => []));
      setRefresh((n) => n + 1);
    } catch (err) { setError(err.message); }
  }

  async function saveEdit(prog) {
    setMessage(""); setError("");
    try {
      const semesters = Array.from({ length: Number(editForm.semester_count || 8) }, (_, i) => ({
        semester_number: i + 1,
        courses: (semesterCourses[i] || []).filter((c) => c.code && c.name && !c.existing_id).map((c) => ({ code: c.code.trim(), name: c.name.trim(), credits: Number(c.credits) || 3, subject_type: "CORE", is_core: true }))
      })).filter((s) => s.courses.length > 0);

      await request(`/admin/programs/${prog.id}/`, token, { method: "PATCH", body: JSON.stringify({ semesters, remove_subject_ids: removedSubjects }) });
      setMessage("✓ Curriculum updated.");
      setEditingId(null);
      setRefresh((n) => n + 1);
    } catch (err) { setError(err.message); }
  }

  function startEdit(prog) {
    setEditingId(prog.id);
    setEditForm({ semester_count: prog.semester_count || 8 });
    
    const currentSemesters = Array.from({ length: prog.semester_count || 8 }, () => []);
    (prog.semesters || []).forEach((sem) => {
      currentSemesters[sem.semester_number - 1] = (sem.courses || []).map((c) => ({
        code: c.code,
        name: c.name,
        credits: c.credits,
        existing_id: c.subject_id,
      }));
    });
    setSemesterCourses(currentSemesters);
    setRemovedSubjects([]);
    setExpanded(null);
  }

  return (
    <section className="panel programs-panel">
      <div className="panel-head">
        <div>
          <span className="eyebrow">PROGRAMS</span>
          <h2>Programs &amp; Curriculum</h2>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span className="count-pill">{programs.length} programs</span>
          <button className="primary-button compact" onClick={() => { setShowCreate((v) => !v); setEditingId(null); }}>{showCreate ? "Cancel" : "＋ New program"}</button>
        </div>
      </div>

      {error && <div className="error-message page-message">{error}</div>}
      {message && <p className="form-message page-message">{message}</p>}

      {showCreate && (
        <div className="program-builder-form">
          <form onSubmit={createProgram}>
            <div className="form-grid">
              <Field label="Program code"><input required value={form.program_code} placeholder="BTECH-CS" onChange={(e) => setForm({ ...form, program_code: e.target.value })} /></Field>
              <Field label="Program name"><input required value={form.program_name} placeholder="B.Tech Computer Science" onChange={(e) => setForm({ ...form, program_name: e.target.value })} /></Field>
              <Field label="Department">
                <select required value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })}>
                  <option value="">Choose department</option>
                  {departments.map((d) => <option key={d.id} value={d.id}>{d.department_code} · {d.department_name}</option>)}
                </select>
              </Field>
              <Field label="Degree type"><input value={form.degree_type} onChange={(e) => setForm({ ...form, degree_type: e.target.value })} /></Field>
              <Field label="Duration (years)"><input type="number" min="1" value={form.duration_years} onChange={(e) => setForm({ ...form, duration_years: e.target.value })} /></Field>
              <Field label="Number of semesters">
                <select value={form.semester_count} onChange={(e) => handleSemCount(e.target.value)}>
                  {Array.from({ length: 12 }, (_, i) => <option key={i + 1} value={i + 1}>{i + 1}</option>)}
                </select>
              </Field>
            </div>
            <div className="semester-builder-section">
              <span className="field-label">Courses by semester</span>
              <div className="semester-blocks">
                {Array.from({ length: Number(form.semester_count) }, (_, si) => (
                  <div className="semester-block" key={si}>
                    <div className="semester-block-head">
                      <span className="semester-label">Semester {si + 1}</span>
                      <button type="button" className="add-course-btn" onClick={() => addCourse(si)}>＋ Add course</button>
                    </div>
                    {(semesterCourses[si] || []).length === 0 && <p className="semester-empty">No courses yet.</p>}
                    {(semesterCourses[si] || []).map((course, ci) => (
                      <div className="course-row" key={ci}>
                        <input className="course-input code" placeholder="Code" value={course.code} onChange={(e) => updateCourse(si, ci, "code", e.target.value)} />
                        <input className="course-input name" placeholder="Course name" value={course.name} onChange={(e) => updateCourse(si, ci, "name", e.target.value)} />
                        <input className="course-input credits" placeholder="Cr" type="number" min="1" max="10" value={course.credits} onChange={(e) => updateCourse(si, ci, "credits", e.target.value)} />
                        <button type="button" className="remove-course-btn" onClick={() => removeCourse(si, ci)}>✕</button>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
            <div className="modal-actions">
              <button type="button" className="secondary-button" onClick={() => setShowCreate(false)}>Cancel</button>
              <button className="primary-button">Create program</button>
            </div>
          </form>
        </div>
      )}

      {programs.length === 0 && !showCreate && <Empty title="No programs yet" text="Click &quot;+ New program&quot; to create the first one." />}

      <div className="program-cards">
        {programs.map((prog) => (
          <div className="program-card" key={prog.id}>
            {editingId === prog.id ? (
              <div className="program-edit-form">
                <div className="program-edit-head">
                  <span className="eyebrow">EDITING CURRICULUM</span>
                  <button className="close-button" onClick={() => setEditingId(null)}>×</button>
                </div>
                <div style={{ marginBottom: 16 }}>
                  <h3 style={{ margin: 0, fontSize: "1.1rem" }}>{prog.program_name}</h3>
                  <span className="muted">{prog.program_code}</span>
                </div>
                <div className="semester-builder-section" style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
                  <span className="field-label">Manage Courses</span>
                  <p className="muted" style={{ marginBottom: 16, fontSize: "0.85rem" }}>Add or remove courses from this program.</p>
                  <div className="semester-blocks">
                    {Array.from({ length: Number(editForm.semester_count || 8) }, (_, si) => (
                      <div className="semester-block" key={si}>
                        <div className="semester-block-head">
                          <span className="semester-label">Semester {si + 1}</span>
                          <button type="button" className="add-course-btn" onClick={() => addCourse(si)}>＋ Add course</button>
                        </div>
                        {(semesterCourses[si] || []).map((course, ci) => (
                          <div className="course-row" key={ci}>
                            <input className="course-input code" placeholder="Code" value={course.code} onChange={(e) => updateCourse(si, ci, "code", e.target.value)} />
                            <input className="course-input name" placeholder="Course name" value={course.name} onChange={(e) => updateCourse(si, ci, "name", e.target.value)} />
                            <input className="course-input credits" placeholder="Cr" type="number" min="1" max="10" value={course.credits} onChange={(e) => updateCourse(si, ci, "credits", e.target.value)} />
                            <button type="button" className="remove-course-btn" onClick={() => removeCourse(si, ci)}>✕</button>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="modal-actions" style={{ marginTop: 16 }}>
                  <button className="secondary-button" onClick={() => setEditingId(null)}>Cancel</button>
                  <button className="primary-button" onClick={() => saveEdit(prog)}>Save changes</button>
                </div>
              </div>
            ) : (
              <>
                <div className="program-card-head" onClick={() => setExpanded(expanded === prog.id ? null : prog.id)}>
                  <div className="program-card-title">
                    <span className="program-code-badge">{prog.program_code}</span>
                    <div>
                      <strong>{prog.program_name}</strong>
                      <small>{prog.degree_type} · {prog.department_name || prog.department} · {prog.duration_years} yrs</small>
                    </div>
                  </div>
                  <div className="program-card-meta">
                    <span className="tag">{prog.semester_count || (prog.semesters && prog.semesters.length) || "—"} sem</span>
                    <span className="tag blue">{prog.course_count || "—"} courses</span>
                    <button className="edit-prog-btn" onClick={(e) => { e.stopPropagation(); startEdit(prog); }}>Edit</button>
                    <span className="chevron">{expanded === prog.id ? "▲" : "▼"}</span>
                  </div>
                </div>
                {expanded === prog.id && (
                  <div className="program-card-body">
                    {(prog.semesters || []).length === 0 && <p className="muted">No semester details available.</p>}
                    {(prog.semesters || []).map((sem) => (
                      <div className="sem-detail" key={sem.id || sem.semester_number}>
                        <span className="sem-detail-label">Semester {sem.semester_number}</span>
                        <div className="sem-courses">
                          {(sem.courses || []).length === 0 && <span className="muted">No courses</span>}
                          {(sem.courses || []).map((c, i) => (
                            <span className="course-chip" key={i}><b>{c.code}</b> {c.name} <em>({c.credits} cr)</em></span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function FacultyView({ id, token }) {
  const configs = { profile: ["/faculty/profile/", "profile"], teaching: ["/faculty/subjects/", "subjects"], attendance: ["/faculty/attendance/reports/", "attendance"], exams: ["/faculty/exams/", "exams"], communication: ["/faculty/posts/", "posts"], leave: ["/faculty/leave-requests/", "leave"] };
  if (id === "overview") return <FacultyDashboard token={token} />;
  if (id === "profile") return <ProfileView token={token} faculty />;
  if (id === "teaching") return <FacultyTeaching token={token} />;
  if (id === "attendance") return <FacultyAttendance token={token} />;
  if (id === "exams") return <FacultyExams token={token} />;
  if (id === "communication") return <FacultyCommunication token={token} />;
  return <LeaveView token={token} faculty />;
}

function FacultyDashboard({ token }) { const [data, setData] = useState(null); useEffect(() => { request("/faculty/dashboard/", token).then(setData).catch(() => setData({})); }, [token]); return <DashboardFrame eyebrow="FACULTY WORKSPACE" title="Your teaching day" description="A focused view of classes, attendance, exams, and the students assigned to you."><Stats items={[{ label: "Subjects assigned", value: data?.subjects_assigned ?? "—", tone: "blue" }, { label: "Students", value: data?.students ?? "—", tone: "green" }, { label: "Pending attendance", value: data?.pending_attendance ?? "—", tone: "yellow" }]} token={token} /><div className="split-grid"><InfoPanel title="Today's classes" kicker="SCHEDULE"><SimpleList items={(data?.today_classes || []).map((item) => `${item.time}  ${item.subject} · ${item.section}`)} empty="No classes scheduled today." /></InfoPanel><InfoPanel title="Upcoming exams" kicker="EXAMINATION"><SimpleList items={(data?.upcoming_exams || []).map((item) => `${item.date}  ${item.subject}`)} empty="No upcoming exams." /></InfoPanel></div></DashboardFrame>; }

function FacultyTeaching({ token }) { 
  const [subjects, setSubjects] = useState([]); 
  const [sections, setSections] = useState([]); 
  const [form, setForm] = useState({ subject: "", section: "", attendance_date: new Date().toISOString().slice(0, 10), start_time: "09:00", end_time: "10:00" });
  const [message, setMessage] = useState("");

  useEffect(() => { 
    Promise.all([request("/faculty/subjects/", token), request("/faculty/sections/", token)]).then(([a, b]) => { 
      setSubjects(a.results || a); 
      setSections(b); 
    }); 
  }, [token]); 
  
  function update(key, value) { setForm({ ...form, [key]: value }); }
  async function submit(event) {
    event.preventDefault();
    try {
      await request("/faculty/attendance/", token, { method: "POST", body: JSON.stringify(form) });
      setMessage("Class scheduled successfully.");
    } catch (err) { setMessage(err.message); }
  }

  return <DashboardFrame eyebrow="TEACHING" title="Your assignments" description="Subject and section assignments are controlled by academic administration."><div className="metric-grid">{subjects.map((item) => <article className="subject-card" key={item.faculty_subject_id}><span className="subject-code">{item.subject_code}</span><h2>{item.subject_name}</h2><p>Semester {item.semester_number} · {item.section_code}</p><small>{item.academic_year_code}</small></article>)}</div><div className="split-grid"><InfoPanel title="Assigned sections" kicker="CLASSES"><DataTable columns={["Section", "Program", "Semester", "Students"]} rows={sections.map((item) => [item.section_code, item.program, item.semester, item.students])} /></InfoPanel><form className="panel compact-form" onSubmit={submit}><div className="panel-head"><div><span className="eyebrow">SCHEDULE</span><h2>Create a class</h2></div><button className="primary-button compact">Schedule</button></div><div className="form-grid"><Field label="Subject"><select required value={form.subject} onChange={(e) => update("subject", e.target.value)}><option value="">Choose subject</option>{subjects.map((item) => <option key={item.faculty_subject_id} value={item.subject}>{item.subject_code} · {item.section_code}</option>)}</select></Field><Field label="Section"><select required value={form.section} onChange={(e) => update("section", e.target.value)}><option value="">Choose section</option>{sections.map((item) => <option key={item.section_id} value={item.section_id}>{item.section_code} · Semester {item.semester}</option>)}</select></Field><Field label="Date"><input type="date" required value={form.attendance_date} onChange={(e) => update("attendance_date", e.target.value)} /></Field><Field label="Start time"><input type="time" required value={form.start_time} onChange={(e) => update("start_time", e.target.value)} /></Field><Field label="End time"><input type="time" required value={form.end_time} onChange={(e) => update("end_time", e.target.value)} /></Field></div>{message && <p className="form-message">{message}</p>}</form></div></DashboardFrame>; 
}

function FacultyAttendance({ token }) { 
  const [report, setReport] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [students, setStudents] = useState([]);
  const [statuses, setStatuses] = useState({});
  const [message, setMessage] = useState("");

  function loadSessions() {
    request("/faculty/attendance/", token).then((data) => setSessions(Array.isArray(data) ? data : []));
  }

  useEffect(() => { 
    request("/faculty/attendance/reports/", token).then(setReport);
    loadSessions();
  }, [token]); 

  useEffect(() => { 
    if (!expanded) return;
    request(`/faculty/sections/${expanded.section_id}/students/`, token).then((items) => { 
      setStudents(items); 
      setStatuses(Object.fromEntries(items.map((item) => [item.student_id, "PRESENT"]))); 
    }); 
  }, [expanded, token]); 

  async function submit(event) { 
    event.preventDefault(); 
    try { 
      await request(`/faculty/attendance/${expanded.attendance_session_id}/`, token, { 
        method: "PATCH", 
        body: JSON.stringify({ 
          status: "COMPLETED",
          records: students.map((student) => ({ student: student.student_id, status: statuses[student.student_id] })) 
        }) 
      }); 
      setMessage(""); 
      setExpanded(null);
      loadSessions();
    } catch (err) { setMessage(err.message); } 
  } 

  return <DashboardFrame eyebrow="ATTENDANCE" title="Attendance at a glance" description="Mark attendance for completed classes."><Stats items={[{ label: "Attendance records", value: report?.total ?? "—", tone: "blue" }, { label: "Present or late", value: report?.present ?? "—", tone: "green" }, { label: "Average attendance", value: report ? `${report.percentage}%` : "—", tone: "yellow" }]} token={token} /><div className="panel"><div className="panel-head"><div><span className="eyebrow">CLASSES</span><h2>Scheduled classes</h2></div></div><div style={{ padding: "0 24px" }}>{sessions.length === 0 ? <p className="panel-copy" style={{ padding: "24px 0" }}>No classes scheduled.</p> : sessions.map((session) => <div key={session.attendance_session_id} style={{ borderBottom: "1px solid var(--line)", padding: "16px 0" }}><div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><div><strong>{session.subject} · {session.section}</strong><div style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>{session.attendance_date} | {session.start_time} - {session.end_time}</div></div>{session.status === "COMPLETED" ? <span style={{ color: "var(--primary-color)", fontSize: "12px", fontWeight: "600", padding: "4px 8px", background: "var(--primary-bg)", borderRadius: "4px" }}>COMPLETED</span> : <button className="primary-button compact" onClick={() => { setExpanded(expanded?.attendance_session_id === session.attendance_session_id ? null : session); setMessage(""); }}>{expanded?.attendance_session_id === session.attendance_session_id ? "Close" : "Take attendance"}</button>}</div>{expanded?.attendance_session_id === session.attendance_session_id && <form className="attendance-form" style={{ marginTop: "16px", padding: "16px", background: "var(--secondary-bg)", borderRadius: "8px" }} onSubmit={submit}><h4 style={{ margin: "0 0 16px 0", fontSize: "14px" }}>Mark Attendance</h4>{message && <p className="form-message">{message}</p>}<div className="attendance-list">{students.map((student) => <div key={student.student_id}><span><strong>{student.roll_number || "—"}</strong> {student.name}</span><div style={{ display: "flex", gap: "12px", fontSize: "12px" }}>{["PRESENT", "ABSENT", "LATE", "EXCUSED"].map(status => <label key={status} style={{ display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}><input type="radio" name={`status-${student.student_id}`} value={status} checked={statuses[student.student_id] === status} onChange={(e) => setStatuses({ ...statuses, [student.student_id]: e.target.value })} />{status}</label>)}</div></div>)}</div><div style={{ marginTop: "16px", display: "flex", gap: "10px" }}><button type="submit" className="primary-button compact">Mark class completed</button><button type="button" className="secondary-button compact" onClick={() => setExpanded(null)}>Cancel</button></div></form>}</div>)}</div></div></DashboardFrame>; 
}

function FacultyExams({ token }) { const [exams, setExams] = useState([]); useEffect(() => { request("/faculty/exams/", token).then(setExams); }, [token]); return <DashboardFrame eyebrow="EXAMINATION" title="Exam schedule" description="Review examinations linked to your assigned subjects and enter marks from the academic workflow."><InfoPanel title="Upcoming and active exams" kicker="SCHEDULE"><DataTable columns={["Exam", "Subject", "Date", "Marks"]} rows={exams.map((item) => [item.exam, item.subject, item.date, `${item.passing_marks}/${item.max_marks}`])} /></InfoPanel></DashboardFrame>; }

function FacultyCommunication({ token }) { 
  const [posts, setPosts] = useState([]); 
  const [sections, setSections] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => { 
    Promise.all([request("/faculty/posts/", token), request("/faculty/sections/", token)]).then(([a, b]) => {
      setPosts(a.results || a);
      setSections(b);
    });
  }, [token]); 
  
  async function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await request("/faculty/posts/", token, { method: "POST", body: JSON.stringify(Object.fromEntries(form.entries())) });
      const newPosts = await request("/faculty/posts/", token);
      setPosts(newPosts.results || newPosts);
      setMessage("Post published successfully.");
      event.currentTarget.reset();
    } catch(err) { setMessage(err.message); }
  }

  return <DashboardFrame eyebrow="COMMUNICATION" title="Class communication" description="Publish updates to the sections assigned to you."><div className="split-grid"><form className="panel compact-form" onSubmit={submit}><span className="eyebrow">NEW POST</span><h2>Create an update</h2><Field label="Section"><select name="section" required><option value="">Choose a section</option>{sections.map((sec) => <option key={sec.section_id} value={sec.section_id}>{sec.section_code} (Sem {sec.semester})</option>)}</select></Field><Field label="Title"><input name="title" required /></Field><Field label="Message"><textarea name="content" required rows="4" /></Field>{message && <p className="form-message">{message}</p>}<button className="primary-button compact">Publish post</button></form><InfoPanel title="Your posts" kicker="SECTION UPDATES"><DataTable columns={["Title", "Visibility", "Created"]} rows={posts.map((item) => [item.title, item.visibility, new Date(item.created_at).toLocaleDateString()])} /></InfoPanel></div></DashboardFrame>; 
}

function StudentView({ id, token }) {
  if (id === "overview") return <StudentDashboard token={token} />;
  if (id === "profile") return <ProfileView token={token} />;
  const pages = { academics: <StudentAcademics token={token} />, attendance: <StudentAttendance token={token} />, exams: <StudentExams token={token} />, fees: <StudentFees token={token} />, library: <StudentLibrary token={token} />, communication: <StudentCommunication token={token} />, requests: <StudentRequests token={token} />, leave: <LeaveView token={token} />, events: <StudentEvents token={token} /> };
  return pages[id];
}

function StudentDashboard({ token }) { const [data, setData] = useState(null); useEffect(() => { request("/student/dashboard/", token).then(setData).catch(() => setData({})); }, [token]); return <DashboardFrame eyebrow="STUDENT PORTAL" title={data?.student?.name ? `Welcome back, ${data.student.name.split(" ")[0]}.` : "Your campus, in view."} description="Everything important about your academic day, brought together."><div className="student-identity"><div><span className="eyebrow">CURRENT ACADEMIC IDENTITY</span><h2>{data?.student?.program || "Program not assigned"}</h2><p>{data?.student?.department || "Department"} · Semester {data?.student?.semester || "—"} · Section {data?.student?.section || "—"}</p></div><span className="identity-number">{data?.student?.roll_number || "—"}<small>ROLL NUMBER</small></span></div><Stats items={[{ label: "Attendance", value: data ? `${data.attendance}%` : "—", tone: "blue" }, { label: "Pending fees", value: data?.pending_fees ?? "—", tone: "yellow" }, { label: "Books issued", value: data?.books_issued ?? "—", tone: "green" }]} token={token} /><InfoPanel title="Next up" kicker="EXAMINATION"><p className="panel-copy">{data?.upcoming_exam ? `${data.upcoming_exam.subject} · ${data.upcoming_exam.date}` : "No upcoming examination is listed."}</p></InfoPanel></DashboardFrame>; }

function ProfileView({ token, faculty = false }) { const endpoint = faculty ? "/faculty/profile/" : "/student/profile/"; const [data, setData] = useState(null); const [message, setMessage] = useState(""); useEffect(() => { request(endpoint, token).then(setData); }, [endpoint, token]); async function save(event) { event.preventDefault(); const form = new FormData(event.currentTarget); const payload = Object.fromEntries(form.entries()); try { await request(endpoint, token, { method: "PATCH", body: JSON.stringify(payload) }); setMessage("Profile updated"); } catch (err) { setMessage(err.message); } } return <DashboardFrame eyebrow="PROFILE" title="Personal details" description={faculty ? "View your institutional identity and update contact details." : "Your academic identity is protected. Update only your personal contact information."}><div className="profile-layout"><InfoPanel title="Identity" kicker="READ ONLY"><div className="identity-list"><span><small>Name</small><b>{data?.name || data?.employee_id || "—"}</b></span><span><small>Department</small><b>{data?.department || "—"}</b></span><span><small>Program</small><b>{data?.program || data?.designation || "—"}</b></span><span><small>{faculty ? "Employee ID" : "Admission number"}</small><b>{data?.employee_id || data?.admission_number || "—"}</b></span></div></InfoPanel><form className="panel edit-panel" onSubmit={save}><span className="eyebrow">EDITABLE</span><h2>Contact details</h2><Field label="Email"><input name="email" type="email" defaultValue={data?.email || ""} /></Field><Field label="Phone"><input name="phone" defaultValue={data?.phone || ""} /></Field>{!faculty && <Field label="Emergency contact"><input name="emergency_contact" defaultValue={data?.emergency_contact || ""} /></Field>}{message && <p className="form-message">{message}</p>}<button className="primary-button compact">Save changes</button></form></div></DashboardFrame>; }

function StudentAcademics({ token }) { const [data, setData] = useState(null); useEffect(() => { request("/student/academics/", token).then(setData); }, [token]); return <DashboardFrame eyebrow="ACADEMICS" title="Your academic structure" description="A read-only view of the program, semester, section, and subjects assigned to you."><div className="student-identity academic"><div><span className="eyebrow">PROGRAM</span><h2>{data?.program || "—"}</h2><p>{data?.department || "—"} · Semester {data?.semester || "—"} · Section {data?.section || "—"}</p></div><span className="identity-number">{data?.academic_year || "—"}<small>ACADEMIC YEAR</small></span></div><InfoPanel title="Semester subjects" kicker="CURRICULUM"><DataTable columns={["Code", "Subject", "Credits", "Type"]} rows={(data?.subjects || []).map((item) => [item.code, item.name, item.credits, item.type || "Core"])} /></InfoPanel></DashboardFrame>; }

function StudentAttendance({ token }) { const [data, setData] = useState(null); useEffect(() => { request("/student/attendance/", token).then(setData); }, [token]); return <DashboardFrame eyebrow="ATTENDANCE" title="Your attendance" description="Attendance is read-only. Contact your faculty if a record needs review."><Stats items={[{ label: "Overall", value: data ? `${data.overall_percentage}%` : "—", tone: "blue" }, { label: "Attended", value: data?.attended ?? "—", tone: "green" }, { label: "Sessions", value: data?.total ?? "—", tone: "yellow" }]} token={token} /><InfoPanel title="Attendance history" kicker="RECENT RECORDS"><DataTable columns={["Date", "Subject", "Status"]} rows={(data?.history || []).map((item) => [item.date, item.subject, item.status])} /></InfoPanel></DashboardFrame>; }

function StudentExams({ token }) { const [exams, setExams] = useState([]); const [marks, setMarks] = useState([]); useEffect(() => { Promise.all([request("/student/exams/", token), request("/student/marks/", token)]).then(([a, b]) => { setExams(a); setMarks(b); }); }, [token]); return <DashboardFrame eyebrow="EXAMINATION" title="Exams and marks" description="Your schedules and published marks, kept together."><InfoPanel title="Exam schedule" kicker="UPCOMING"><DataTable columns={["Exam", "Subject", "Date", "Marks"]} rows={exams.map((item) => [item.exam, item.subject, item.date, `${item.passing_marks}/${item.max_marks}`])} /></InfoPanel><InfoPanel title="Published marks" kicker="RESULTS"><DataTable columns={["Exam", "Subject", "Obtained"]} rows={marks.map((item) => [item.exam, item.subject, item.marks_obtained])} /></InfoPanel></DashboardFrame>; }

function StudentFees({ token }) { const [summary, setSummary] = useState(null); const [invoices, setInvoices] = useState([]); const [message, setMessage] = useState(""); useEffect(() => { Promise.all([request("/student/fees/summary/", token), request("/student/fees/invoices/", token)]).then(([a, b]) => { setSummary(a); setInvoices(b); }); }, [token]); async function pay(invoice) { try { const result = await request("/student/fees/payments/", token, { method: "POST", body: JSON.stringify({ invoice: invoice.invoice_id }) }); setMessage(`Payment ${result.status.toLowerCase()} for ${invoice.invoice_number}.`); } catch (err) { setMessage(err.message); } } return <DashboardFrame eyebrow="FEES" title="Your fee statement" description="View invoices and payment status. Amounts are controlled by the institution."><Stats items={[{ label: "Total fees", value: summary?.total ?? "—", tone: "blue" }, { label: "Paid", value: summary?.paid ?? "—", tone: "green" }, { label: "Pending", value: summary?.pending ?? "—", tone: "yellow" }]} token={token} />{message && <div className="form-message page-message">{message}</div>}<InfoPanel title="Invoices" kicker="STATEMENT"><div className="data-table"><table><thead><tr><th>Invoice</th><th>Due date</th><th>Total</th><th>Status</th><th /></tr></thead><tbody>{invoices.map((item) => <tr key={item.invoice_id}><td>{item.invoice_number}</td><td>{item.due_date}</td><td>{item.total_amount}</td><td>{item.status}</td><td>{item.status !== "PAID" && <button className="text-button" onClick={() => pay(item)}>Start payment</button>}</td></tr>)}</tbody></table>{!invoices.length && <Empty title="No invoices yet" text="Your institution has not published a fee invoice." />}</div></InfoPanel></DashboardFrame>; }

function StudentLibrary({ token }) { const [books, setBooks] = useState([]); const [issues, setIssues] = useState([]); const [message, setMessage] = useState(""); useEffect(() => { Promise.all([request("/student/library/books/", token), request("/student/library/issues/", token)]).then(([a, b]) => { setBooks(a); setIssues(b); }); }, [token]); async function renew(issue) { try { const result = await request(`/student/library/issues/${issue.issue_id}/renew/`, token, { method: "POST", body: "{}" }); setIssues(issues.map((item) => item.issue_id === issue.issue_id ? { ...item, due_date: result.due_date, status: result.status } : item)); } catch (err) { setMessage(err.message); } } return <DashboardFrame eyebrow="LIBRARY" title="Library desk" description="Search the catalogue and keep an eye on your issued books.">{message && <div className="error-message page-message">{message}</div>}<div className="split-grid"><InfoPanel title="My issued books" kicker="LOANS"><div className="data-table"><table><thead><tr><th>Book</th><th>Due date</th><th>Status</th><th /></tr></thead><tbody>{issues.map((item) => <tr key={item.issue_id}><td>{item.book}</td><td>{item.due_date}</td><td>{item.status}</td><td>{!item.return_date && <button className="text-button" onClick={() => renew(item)}>Renew</button>}</td></tr>)}</tbody></table>{!issues.length && <Empty title="No books issued" text="Your active loans will appear here." />}</div></InfoPanel><InfoPanel title="Catalogue" kicker="SEARCH"><DataTable columns={["Title", "Author", "Available"]} rows={books.slice(0, 8).map((item) => [item.title, item.author, item.available])} /></InfoPanel></div></DashboardFrame>; }

function StudentCommunication({ token }) { const [notices, setNotices] = useState([]); const [posts, setPosts] = useState([]); useEffect(() => { Promise.all([request("/student/notices/", token), request("/student/posts/", token)]).then(([a, b]) => { setNotices(a); setPosts(b); }); }, [token]); return <DashboardFrame eyebrow="COMMUNICATION" title="Campus updates" description="Notices and posts targeted to you and your section."><div className="split-grid"><InfoPanel title="Notices" kicker="INBOX"><SimpleList items={notices.map((item) => item.title)} empty="No notices yet." /></InfoPanel><InfoPanel title="Posts" kicker="SECTION FEED"><SimpleList items={posts.map((item) => item.title)} empty="No posts yet." /></InfoPanel></div></DashboardFrame>; }

function StudentRequests({ token }) { const [items, setItems] = useState([]); const [error, setError] = useState(""); useEffect(() => { request("/student/requests/", token).then((data) => setItems(data.results || data)); }, [token]); async function submit(event) { event.preventDefault(); const form = new FormData(event.currentTarget); try { await request("/student/requests/", token, { method: "POST", body: JSON.stringify(Object.fromEntries(form.entries())) }); setItems(await request("/student/requests/", token)); event.currentTarget.reset(); } catch (err) { setError(err.message); } } return <DashboardFrame eyebrow="REQUESTS" title="Student services" description="Submit a request and follow its progress without visiting another office."><div className="split-grid"><form className="panel compact-form" onSubmit={submit}><span className="eyebrow">NEW REQUEST</span><h2>Request a document</h2><Field label="Request type"><select name="request_type" defaultValue="BONAFIDE"><option>BONAFIDE</option><option>TRANSCRIPT</option><option>ID_CARD</option><option>TRANSFER_CERTIFICATE</option></select></Field><Field label="Details"><textarea name="description" required rows="4" /></Field>{error && <div className="error-message">{error}</div>}<button className="primary-button compact">Submit request</button></form><InfoPanel title="Your requests" kicker="STATUS"><DataTable columns={["Type", "Submitted", "Status"]} rows={items.map((item) => [item.request_type, item.submitted_at, item.status])} /></InfoPanel></div></DashboardFrame>; }

function LeaveView({ token, faculty = false }) { const endpoint = faculty ? "/faculty/leave-requests/" : "/student/leave/"; const [items, setItems] = useState([]); const [types, setTypes] = useState([]); useEffect(() => { request(endpoint, token).then((data) => setItems(data.results || data)); }, [endpoint, token]); async function submit(event) { event.preventDefault(); const form = new FormData(event.currentTarget); try { await request(endpoint, token, { method: "POST", body: JSON.stringify(Object.fromEntries(form.entries())) }); setItems(await request(endpoint)); event.currentTarget.reset(); } catch (err) { window.alert(err.message); } } return <DashboardFrame eyebrow="LEAVE" title="Leave requests" description="Submit leave and track its approval status."><div className="split-grid"><form className="panel compact-form" onSubmit={submit}><span className="eyebrow">NEW APPLICATION</span><h2>Apply for leave</h2><Field label="Leave type"><input name="leave_type" type="number" placeholder="Leave type ID" required /></Field><Field label="From"><input name="start_date" type="date" required /></Field><Field label="To"><input name="end_date" type="date" required /></Field><Field label="Reason"><textarea name="reason" required rows="3" /></Field><button className="primary-button compact">Submit application</button></form><InfoPanel title="History" kicker="TRACKING"><DataTable columns={["From", "To", "Status"]} rows={items.map((item) => [item.start_date, item.end_date, item.status])} /></InfoPanel></div></DashboardFrame>; }

function StudentEvents({ token }) { const [events, setEvents] = useState([]); const [clubs, setClubs] = useState([]); useEffect(() => { Promise.all([request("/student/events/", token), request("/student/clubs/", token)]).then(([a, b]) => { setEvents(a); setClubs(b); }); }, [token]); async function register(id) { await request(`/student/events/${id}/register/`, token, { method: "POST", body: "{}" }); } async function join(id) { await request(`/student/clubs/${id}/join/`, token, { method: "POST", body: "{}" }); } return <DashboardFrame eyebrow="CAMPUS LIFE" title="Events and clubs" description="Find the things happening beyond the timetable."><div className="split-grid"><InfoPanel title="Upcoming events" kicker="EVENTS"><div className="event-list">{events.map((item) => <div className="event-row" key={item.event_id}><span className="event-date">{new Date(item.start_at).toLocaleDateString("en", { day: "2-digit", month: "short" })}</span><span><strong>{item.name}</strong><small>{item.venue}</small></span><button className="text-button" onClick={() => register(item.event_id)}>Register</button></div>)}</div></InfoPanel><InfoPanel title="Clubs" kicker="MEMBERSHIPS"><div className="event-list">{clubs.map((item) => <div className="event-row" key={item.club_id}><span className="club-dot">✦</span><span><strong>{item.name}</strong><small>{item.description}</small></span><button className="text-button" onClick={() => join(item.club_id)}>Join</button></div>)}</div></InfoPanel></div></DashboardFrame>; }

function LibrarianView({ id, token }) {
  if (id === "overview") return <LibrarianDashboard token={token} />;
  if (id === "profile") return <ProfileView token={token} faculty />;
  if (id === "books") return <LibrarianBooks token={token} />;
  if (id === "circulation") return <LibrarianCirculation token={token} />;
  if (id === "reservations") return <LibrarianReservations token={token} />;
  if (id === "fines") return <LibrarianFines token={token} />;
  if (id === "members") return <LibrarianMembers token={token} />;
  if (id === "inventory") return <LibrarianInventory token={token} />;
  if (id === "communication") return <LibrarianNotices token={token} />;
  return <LibrarianReports token={token} />;
}

function useLibraryData(token) {
  const [books, setBooks] = useState([]);
  const [loans, setLoans] = useState([]);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    Promise.all([request("/books/", token), request("/loans/", token)])
      .then(([bookData, loanData]) => { setBooks(bookData.results || bookData); setLoans(loanData.results || loanData); })
      .catch((err) => setError(err.message));
  }, [token, refresh]);
  return { books, loans, error, reload: () => setRefresh((value) => value + 1) };
}

function LibrarianDashboard({ token }) {
  const { books, loans, error } = useLibraryData(token);
  const issued = loans.filter((loan) => !loan.returned_on).length;
  const available = books.reduce((sum, book) => sum + Number(book.copies_available || 0), 0);
  return <DashboardFrame eyebrow="LIBRARY OPERATIONS" title="The library, in motion." description="A working view of inventory, circulation, and the people relying on it.">{error && <div className="error-message">{error}</div>}<Stats items={[{ label: "Book titles", value: books.length, tone: "blue" }, { label: "Available copies", value: available, tone: "green" }, { label: "Current issues", value: issued, tone: "yellow" }]} /><div className="split-grid"><InfoPanel title="Today's focus" kicker="LIBRARY DESK"><div className="mini-list"><span><b>01</b> Search a member before issuing</span><span><b>02</b> Confirm copy condition on return</span><span><b>03</b> Review overdue circulation daily</span></div></InfoPanel><InfoPanel title="Quick actions" kicker="CIRCULATION"><div className="quick-actions"><button className="action-link">Issue a book <span>↗</span></button><button className="action-link">Record a return <span>↗</span></button></div></InfoPanel></div></DashboardFrame>;
}

function LibrarianBooks({ token }) {
  const { books, error, reload } = useLibraryData(token);
  const [query, setQuery] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [message, setMessage] = useState("");
  const visible = books.filter((book) => `${book.title} ${book.author} ${book.isbn}`.toLowerCase().includes(query.toLowerCase()));
  async function create(event) { event.preventDefault(); const form = new FormData(event.currentTarget); try { await request("/books/", token, { method: "POST", body: JSON.stringify({ title: form.get("title"), author: form.get("author"), isbn: form.get("isbn"), copies_total: Number(form.get("copies_total")), copies_available: Number(form.get("copies_total")) }) }); setShowForm(false); setMessage("Book title added to the catalogue."); reload(); } catch (err) { setMessage(err.message); } }
  return <DashboardFrame eyebrow="LIBRARY MANAGEMENT" title="Books and copies" description="Manage the catalogue at title level. Physical circulation is tracked through copies and loans."><div className="toolbar"><div className="search-box"><span>⌕</span><input placeholder="Search title, author, ISBN" value={query} onChange={(event) => setQuery(event.target.value)} /></div><button className="primary-button compact" onClick={() => setShowForm(true)}>＋ Add book</button></div>{error && <div className="error-message">{error}</div>}{message && <p className="form-message page-message">{message}</p>}{showForm && <div className="panel compact-form"><form className="form-grid" onSubmit={create}><Field label="Title"><input name="title" required /></Field><Field label="Author"><input name="author" required /></Field><Field label="ISBN"><input name="isbn" required /></Field><Field label="Copies"><input name="copies_total" type="number" min="1" defaultValue="1" required /></Field><div className="modal-actions full"><button type="button" className="secondary-button" onClick={() => setShowForm(false)}>Cancel</button><button className="primary-button">Add to catalogue</button></div></form></div>}<InfoPanel title="Catalogue" kicker={`${visible.length} TITLES`}><DataTable columns={["Title", "Author", "ISBN", "Total", "Available"]} rows={visible.map((book) => [book.title, book.author, book.isbn, book.copies_total, book.copies_available])} /></InfoPanel></DashboardFrame>;
}

function LibrarianCirculation({ token }) {
  const { loans, error, reload } = useLibraryData(token);
  const [busy, setBusy] = useState("");
  async function returnBook(loan) { setBusy(loan.id); try { await request(`/loans/${loan.id}/return-book/`, token, { method: "POST", body: "{}" }); reload(); } catch (err) { window.alert(err.message); } finally { setBusy(""); } }
  async function renew(loan) { const due = window.prompt("New due date (YYYY-MM-DD)", loan.due_on); if (!due) return; try { await request(`/loans/${loan.id}/reissue/`, token, { method: "POST", body: JSON.stringify({ due_on: due }) }); reload(); } catch (err) { window.alert(err.message); } }
  const active = loans.filter((loan) => !loan.returned_on);
  return <DashboardFrame eyebrow="CIRCULATION" title="Issue and return desk" description="Keep every physical copy accountable from checkout to return.">{error && <div className="error-message">{error}</div>}<Stats items={[{ label: "Current issues", value: active.length, tone: "blue" }, { label: "Returned records", value: loans.length - active.length, tone: "green" }, { label: "Overdue review", value: active.filter((loan) => loan.due_on && new Date(loan.due_on) < new Date()).length, tone: "yellow" }]} /><InfoPanel title="Active circulation" kicker="CURRENT ISSUES"><div className="data-table"><table><thead><tr><th>Book</th><th>Borrower</th><th>Issued</th><th>Due</th><th>Actions</th></tr></thead><tbody>{active.map((loan) => <tr key={loan.id}><td>{loan.book}</td><td>{loan.borrower}</td><td>{loan.issued_on}</td><td>{loan.due_on}</td><td><div className="row-actions"><button onClick={() => renew(loan)}>Renew</button><button onClick={() => returnBook(loan)} disabled={busy === loan.id}>{busy === loan.id ? "Saving..." : "Return"}</button></div></td></tr>)}</tbody></table>{!active.length && <Empty title="No active loans" text="Issued books will appear here." />}</div></InfoPanel></DashboardFrame>;
}

function LibrarianReservations({ token }) { return <DashboardFrame eyebrow="CIRCULATION" title="Reservations" description="Process holds and prepare requested titles for pickup."><InfoPanel title="Reservation queue" kicker="PENDING"><Empty title="No reservation endpoint yet" text="The backend reservation workflow is ready for its librarian API integration." /></InfoPanel></DashboardFrame>; }
function LibrarianFines({ token }) { return <DashboardFrame eyebrow="CIRCULATION" title="Fines" description="Review outstanding charges and keep resolution auditable."><InfoPanel title="Fine history" kicker="ACCOUNTABILITY"><Empty title="No fine records yet" text="Fine calculation and waiver actions will appear when the librarian API is enabled." /></InfoPanel></DashboardFrame>; }
function LibrarianMembers({ token }) { const { loans } = useLibraryData(token); const members = [...new Map(loans.map((loan) => [loan.borrower, loan])).values()]; return <DashboardFrame eyebrow="MEMBERS" title="Library members" description="Search the circulation history of students and staff without changing their institutional accounts."><InfoPanel title="Borrowers in circulation" kicker="MEMBER ACTIVITY"><DataTable columns={["Member", "Active books", "Latest due date"]} rows={members.map((member) => [member.borrower, loans.filter((loan) => loan.borrower === member.borrower && !loan.returned_on).length, member.due_on])} /></InfoPanel></DashboardFrame>; }
function LibrarianInventory({ token }) { const { books } = useLibraryData(token); const total = books.reduce((sum, book) => sum + Number(book.copies_total || 0), 0); const available = books.reduce((sum, book) => sum + Number(book.copies_available || 0), 0); return <DashboardFrame eyebrow="INVENTORY" title="Inventory health" description="A quick view of title and copy counts. Copy incidents will be tracked through the library API as it is enabled."><Stats items={[{ label: "Titles", value: books.length, tone: "blue" }, { label: "Total copies", value: total, tone: "green" }, { label: "In circulation", value: total - available, tone: "yellow" }]} /><InfoPanel title="Inventory notes" kicker="AUDIT"><p className="panel-copy">Use accession numbers and copy status for lost, damaged, missing, maintenance, and disposed items. The current backend exposes title-level books and loans; physical copy incidents are reserved for the next library API slice.</p></InfoPanel></DashboardFrame>; }
function LibrarianNotices({ token }) { return <DashboardFrame eyebrow="COMMUNICATION" title="Library notices" description="Prepare library-specific updates for members and the campus community."><InfoPanel title="Notice composer" kicker="LIBRARY CHANNEL"><p className="panel-copy">Library notices will target members without granting access to college-wide administration.</p><button className="primary-button compact" onClick={() => window.alert("Library notice creation will connect when the librarian notice endpoint is enabled.")}>Compose notice</button></InfoPanel></DashboardFrame>; }
function LibrarianReports({ token }) { const { books, loans } = useLibraryData(token); return <DashboardFrame eyebrow="REPORTS" title="Library reports" description="Scan circulation and inventory signals from one operational view."><Stats items={[{ label: "Titles", value: books.length, tone: "blue" }, { label: "Issues recorded", value: loans.length, tone: "green" }, { label: "Open issues", value: loans.filter((loan) => !loan.returned_on).length, tone: "yellow" }]} /><InfoPanel title="Report coverage" kicker="AVAILABLE NOW"><div className="mini-list"><span><b>01</b> Title and copy availability</span><span><b>02</b> Current and returned loans</span><span><b>03</b> Overdue review from due dates</span></div></InfoPanel></DashboardFrame>; }

function DashboardFrame({ eyebrow, title, description, children }) { return <><div className="page-intro"><span className="eyebrow">{eyebrow}</span><h2>{title}</h2><p>{description}</p></div>{children}</>; }
function Stats({ items }) { return <div className="stats-grid">{items.map((item) => <div className={`stat-card ${item.tone || "blue"}`} key={item.label}><span>{item.label}</span><strong>{item.value ?? "—"}</strong><small>{item.hint || "Current view"}</small></div>)}</div>; }
function InfoPanel({ title, kicker, children }) { return <section className="panel"><div className="panel-head"><div><span className="eyebrow">{kicker}</span><h2>{title}</h2></div></div>{children}</section>; }
function DataTable({ columns, rows }) { return rows.length ? <div className="data-table"><table><thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{String(cell ?? "—")}</td>)}</tr>)}</tbody></table></div> : <Empty title="Nothing here yet" text="Records will appear when your institution adds them." />; }
function SimpleList({ items, empty }) { return items.length ? <div className="simple-list">{items.map((item, index) => <div key={index}><span className="list-index">{String(index + 1).padStart(2, "0")}</span><strong>{item}</strong></div>)}</div> : <Empty title={empty} text="" />; }
function Empty({ title, text }) { return <div className="empty-state"><strong>{title}</strong>{text && <span>{text}</span>}</div>; }
function Field({ label, children }) { return <label className="field"><span className="field-label">{label}</span>{children}</label>; }
function initials(item) { return `${(item.first_name || item.username || "U")[0]}${item.last_name ? item.last_name[0] : ""}`.toUpperCase(); }
function Icon({ name }) { return <span className="nav-icon" aria-hidden="true">{({ HOME: "⌂", USERS: "◎", PERSON: "○", BOOK: "▤", CHECK: "✓", EXAM: "◇", CHAT: "□", CAL: "▦", CARD: "▱", FILE: "▤", STAR: "✦", BOX: "▥", CHART: "▥" })[name] || "·"}</span>; }
