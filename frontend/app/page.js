"use client";

import { useEffect, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const NAV = {
  ADMIN: [
    ["users", "User management", "USERS"],
    ["academic", "Academic assignments", "BOOK"],
    ["programs", "Programs & curriculum", "FILE"],
    ["communication", "Posts", "CHAT"],
  ],
  FACULTY: [
    ["teaching", "Teaching", "BOOK"],
    ["attendance", "Attendance", "CHECK"],
    ["communication", "Posts", "CHAT"],
  ],
  STUDENT: [
    ["profile", "My profile", "PERSON"],
    ["attendance", "My attendance", "CHECK"],
    ["communication", "Posts", "CHAT"],
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

  const role = user.role || "NONE";
  const navigation = NAV[role] || [];

  if (navigation.length === 0) {
    return (
      <div className="app-shell">
        <aside className="sidebar">
          <div className="brand"><span className="mark">C</span><span>Campus<em>ERP</em></span></div>
          <div className="sidebar-foot" style={{ marginTop: "auto" }}><div className="avatar">{initials(user)}</div><div><strong>{user.first_name || user.username}</strong><small>{user.email || role}</small></div><button className="logout" title="Sign out" onClick={logout}>↗</button></div>
        </aside>
        <main className="main-content">
          <div className="content-wrap"><div className="page-intro"><span className="eyebrow">ACCESS DENIED</span><h2>No portal for this role.</h2><p>Student features have been removed per requirements.</p></div></div>
        </main>
      </div>
    );
  }

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
  if (role === "ADMIN") {
    if (id === "users") return <AdminUsers token={token} />;
    if (id === "academic") return <><DepartmentBuilder token={token} /><ProgramsPanel token={token} /><AdminAcademic token={token} /></>;
    if (id === "programs") return <><DepartmentBuilder token={token} /><ProgramsPanel token={token} /></>;
    if (id === "communication") return <AdminPosts token={token} />;
    return <AdminUsers token={token} />;
  }
  if (role === "FACULTY") return <FacultyView id={id} token={token} />;
  if (role === "STUDENT") return <StudentView id={id} token={token} />;
  return <div className="page-intro"><span className="eyebrow">ACCESS DENIED</span><h2>No portal for this role.</h2></div>;
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
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", phone: "", username: "", password: "", roles: ["STUDENT"], admission_number: "", roll_number: "", employee_code: "" });
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
      else if (form.roles.includes("FACULTY") || form.roles.includes("ADMIN")) { 
        profile_data.employee_code = form.employee_code; 
        username = form.employee_code.toString();
      }

      await request("/admin/users/", token, { method: "POST", body: JSON.stringify({ ...form, username, profile_data }) }); 
      done(); 
    } catch (err) { setError(err.message); } 
  }

  const roleOpts = ["STUDENT", "FACULTY", "ADMIN"];

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
            {(form.roles.includes("FACULTY") || form.roles.includes("ADMIN")) && (
              <>
                <Field label="Employee code"><input type="number" required value={form.employee_code} onChange={(e) => update("employee_code", e.target.value)} /></Field>
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

function AdminPosts({ token }) {
  const [posts, setPosts] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    request("/posts/", token).then((data) => setPosts(data.results || data)).catch(() => {});
  }, [token]);

  async function submitPost(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await request("/posts/", token, { method: "POST", body: JSON.stringify(Object.fromEntries(form.entries())) });
      const data = await request("/posts/", token);
      setPosts(data.results || data);
      setMessage("Post published successfully.");
      event.currentTarget.reset();
    } catch(err) { setMessage(err.message); }
  }

  return <DashboardFrame eyebrow="COMMUNICATION" title="Campus posts" description="Publish posts visible to the entire campus.">{message && <div className="form-message page-message">{message}</div>}<div className="split-grid"><form className="panel compact-form" onSubmit={submitPost}><span className="eyebrow">NEW POST</span><h2>Publish a post</h2><Field label="Title"><input name="title" required /></Field><Field label="Visibility"><select name="visibility" required defaultValue="ALL"><option value="ALL">Everyone</option></select></Field><Field label="Content"><textarea name="content" required rows="4" /></Field><button className="primary-button compact">Publish post</button></form><InfoPanel title="Recent posts" kicker="FEED"><DataTable columns={["Title", "Visibility", "Published"]} rows={posts.map((item) => [item.title, item.visibility, new Date(item.created_at).toLocaleDateString()])} /></InfoPanel></div></DashboardFrame>;
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
  if (id === "teaching") return <FacultyTeaching token={token} />;
  if (id === "attendance") return <FacultyAttendance token={token} />;
  if (id === "communication") return <FacultyCommunication token={token} />;
  return <FacultyTeaching token={token} />;
}

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

  return <DashboardFrame eyebrow="ATTENDANCE" title="Attendance at a glance" description="Mark attendance for completed classes."><div className="panel"><div className="panel-head"><div><span className="eyebrow">CLASSES</span><h2>Scheduled classes</h2></div></div><div style={{ padding: "0 24px" }}>{sessions.length === 0 ? <p className="panel-copy" style={{ padding: "24px 0" }}>No classes scheduled.</p> : sessions.map((session) => <div key={session.attendance_session_id} style={{ borderBottom: "1px solid var(--line)", padding: "16px 0" }}><div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><div><strong>{session.subject} · {session.section}</strong><div style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>{session.attendance_date} | {session.start_time} - {session.end_time}</div></div>{session.status === "COMPLETED" ? <span style={{ color: "var(--primary-color)", fontSize: "12px", fontWeight: "600", padding: "4px 8px", background: "var(--primary-bg)", borderRadius: "4px" }}>COMPLETED</span> : <button className="primary-button compact" onClick={() => { setExpanded(expanded?.attendance_session_id === session.attendance_session_id ? null : session); setMessage(""); }}>{expanded?.attendance_session_id === session.attendance_session_id ? "Close" : "Take attendance"}</button>}</div>{expanded?.attendance_session_id === session.attendance_session_id && <form className="attendance-form" style={{ marginTop: "16px", padding: "16px", background: "var(--secondary-bg)", borderRadius: "8px" }} onSubmit={submit}><h4 style={{ margin: "0 0 16px 0", fontSize: "14px" }}>Mark Attendance</h4>{message && <p className="form-message">{message}</p>}<div className="attendance-list">{students.map((student) => <div key={student.student_id}><span><strong>{student.roll_number || "—"}</strong> {student.name}</span><div style={{ display: "flex", gap: "12px", fontSize: "12px" }}>{["PRESENT", "ABSENT", "LATE", "EXCUSED"].map(status => <label key={status} style={{ display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}><input type="radio" name={`status-${student.student_id}`} value={status} checked={statuses[student.student_id] === status} onChange={(e) => setStatuses({ ...statuses, [student.student_id]: e.target.value })} />{status}</label>)}</div></div>)}</div><div style={{ marginTop: "16px", display: "flex", gap: "10px" }}><button type="submit" className="primary-button compact">Mark class completed</button><button type="button" className="secondary-button compact" onClick={() => setExpanded(null)}>Cancel</button></div></form>}</div>)}</div></div></DashboardFrame>; 
}



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

function DashboardFrame({ eyebrow, title, description, children }) { return <><div className="page-intro"><span className="eyebrow">{eyebrow}</span><h2>{title}</h2><p>{description}</p></div>{children}</>; }
function Stats({ items }) { return <div className="stats-grid">{items.map((item) => <div className={`stat-card ${item.tone || "blue"}`} key={item.label}><span>{item.label}</span><strong>{item.value ?? "—"}</strong><small>{item.hint || "Current view"}</small></div>)}</div>; }
function InfoPanel({ title, kicker, children }) { return <section className="panel"><div className="panel-head"><div><span className="eyebrow">{kicker}</span><h2>{title}</h2></div></div>{children}</section>; }
function DataTable({ columns, rows }) { return rows.length ? <div className="data-table"><table><thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{String(cell ?? "—")}</td>)}</tr>)}</tbody></table></div> : <Empty title="Nothing here yet" text="Records will appear when your institution adds them." />; }
function SimpleList({ items, empty }) { return items.length ? <div className="simple-list">{items.map((item, index) => <div key={index}><span className="list-index">{String(index + 1).padStart(2, "0")}</span><strong>{item}</strong></div>)}</div> : <Empty title={empty} text="" />; }
function Empty({ title, text }) { return <div className="empty-state"><strong>{title}</strong>{text && <span>{text}</span>}</div>; }
function Field({ label, children }) { return <label className="field"><span className="field-label">{label}</span>{children}</label>; }
function initials(item) { return `${(item.first_name || item.username || "U")[0]}${item.last_name ? item.last_name[0] : ""}`.toUpperCase(); }
function Icon({ name }) { return <span className="nav-icon" aria-hidden="true">{({ HOME: "⌂", USERS: "◎", PERSON: "○", BOOK: "▤", CHECK: "✓", EXAM: "◇", CHAT: "□", CAL: "▦", CARD: "▱", FILE: "▤", STAR: "✦", BOX: "▥", CHART: "▥" })[name] || "·"}</span>; }

function StudentView({ id, token }) {
  if (id === "profile") return <StudentProfile token={token} />;
  if (id === "attendance") return <StudentAttendance token={token} />;
  if (id === "communication") return <StudentPosts token={token} />;
  return <StudentProfile token={token} />;
}

function StudentProfile({ token }) {
  const [data, setData] = useState(null);
  useEffect(() => { request("/student/profile/", token).then(setData); }, [token]);
  
  return (
    <DashboardFrame eyebrow="PROFILE" title="Personal details" description="Your academic identity is protected. This is a read-only view.">
      <div className="profile-layout">
        <InfoPanel title="Identity" kicker="READ ONLY">
          <div className="identity-list">
            <span><small>Name</small><b>{data?.name || "—"}</b></span>
            <span><small>Program</small><b>{data?.program || "—"}</b></span>
            <span><small>Department</small><b>{data?.department || "—"}</b></span>
            <span><small>Admission Number</small><b>{data?.admission_number || "—"}</b></span>
            <span><small>Roll Number</small><b>{data?.roll_number || "—"}</b></span>
            <span><small>Semester</small><b>{data?.semester || "—"}</b></span>
            <span><small>Status</small><b>{data?.status || "—"}</b></span>
          </div>
        </InfoPanel>
        <InfoPanel title="Contact" kicker="INFO">
          <div className="identity-list">
            <span><small>Email</small><b>{data?.email || "—"}</b></span>
            <span><small>Phone</small><b>{data?.phone || "—"}</b></span>
            <span><small>Guardian</small><b>{data?.guardian_name || "—"}</b></span>
            <span><small>Guardian Phone</small><b>{data?.guardian_phone || "—"}</b></span>
          </div>
        </InfoPanel>
      </div>
    </DashboardFrame>
  );
}

function StudentAttendance({ token }) {
  const [data, setData] = useState(null);
  useEffect(() => { request("/student/attendance/", token).then(setData); }, [token]);
  
  return (
    <DashboardFrame eyebrow="ATTENDANCE" title="Your attendance" description="Attendance is read-only. Contact your faculty if a record needs review.">
      <Stats items={[
        { label: "Overall", value: data ? `${data.overall_percentage}%` : "—", tone: "blue" },
        { label: "Attended", value: data?.attended ?? "—", tone: "green" },
        { label: "Total Sessions", value: data?.total ?? "—", tone: "yellow" }
      ]} token={token} />
      <InfoPanel title="Attendance history" kicker="RECENT RECORDS">
        <DataTable columns={["Date", "Subject", "Status"]} rows={(data?.history || []).map((item) => [item.date, item.subject, item.status])} />
      </InfoPanel>
    </DashboardFrame>
  );
}

function StudentPosts({ token }) {
  const [posts, setPosts] = useState([]);
  useEffect(() => { request("/student/posts/", token).then(setPosts); }, [token]);
  
  return (
    <DashboardFrame eyebrow="COMMUNICATION" title="Campus posts" description="Announcements from your faculty and administration.">
      <div className="split-grid">
        <InfoPanel title="Recent posts" kicker="FEED">
          {posts.length === 0 ? <Empty title="No posts yet" text="Check back later for announcements." /> : posts.map((post) => (
            <div key={post.post_id} className="post-card" style={{ padding: "16px", borderBottom: "1px solid var(--line)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                <h3 style={{ margin: 0, fontSize: "16px" }}>{post.title}</h3>
                <span className="tag">{new Date(post.created_at).toLocaleDateString()}</span>
              </div>
              <p style={{ margin: "0 0 12px 0", color: "var(--text-secondary)", fontSize: "14px", lineHeight: "1.5" }}>{post.content}</p>
              <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}><strong>Posted by:</strong> {post.author}</div>
            </div>
          ))}
        </InfoPanel>
      </div>
    </DashboardFrame>
  );
}
