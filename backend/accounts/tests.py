from django.test import TestCase
from rest_framework.test import APITestCase

from academics.models import AcademicYear, Course, Exam, ExamSubject, ExamType, FacultySubject, Program, ProgramSubject, Section, Semester, Subject, SectionStudent
from attendance.models import AttendanceSession, LeaveType, StudentAttendance
from fees.models import FeeCategory, FeeInvoice, StudentFeeAccount
from .models import AuditLog, Role, User, UserRole

class AdminUserManagementTests(APITestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username="admin",
			email="admin@example.com",
			password="AdminPass123",
			role=User.Role.ADMIN,
		)
		admin_role = Role.objects.get(role_code=User.Role.ADMIN)
		UserRole.objects.get_or_create(user=self.admin, role=admin_role)
		self.client.force_authenticate(self.admin)

	def test_admin_can_create_user_with_multiple_roles(self):
		response = self.client.post(
			"/api/admin/users/",
			{
				"first_name": "Rahul",
				"last_name": "Sharma",
				"email": "rahul@example.com",
				"phone": "9876543210",
				"username": "rahul.sharma",
				"password": "TempPass123",
				"roles": ["FACULTY", "LIBRARIAN"],
			},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["roles"], ["FACULTY", "LIBRARIAN"])
		created = User.objects.get(username="rahul.sharma")
		self.assertTrue(created.check_password("TempPass123"))
		self.assertFalse("password" in response.data)
		self.assertEqual(created.person.first_name, "Rahul")
		self.assertEqual(AuditLog.objects.filter(action="CREATE_USER").count(), 1)

	def test_admin_can_filter_and_change_status(self):
		user = User.objects.create_user(
			username="priya",
			email="priya@example.com",
			password="TempPass123",
			role=User.Role.PARENT,
		)
		parent_role = Role.objects.get(role_code=User.Role.PARENT)
		UserRole.objects.get_or_create(user=user, role=parent_role)

		response = self.client.get("/api/admin/users/?role=PARENT&status=active&name=priya")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["count"], 1)

		response = self.client.patch(f"/api/admin/users/{user.pk}/status/", {"is_active": False}, format="json")
		self.assertEqual(response.status_code, 200)
		user.refresh_from_db()
		self.assertFalse(user.is_active)
		self.assertTrue(AuditLog.objects.filter(action="DEACTIVATE_USER", entity_id=str(user.pk)).exists())

	def test_admin_can_change_roles_and_reset_password(self):
		user = User.objects.create_user(
			username="rahul",
			email="rahul2@example.com",
			password="OldPass123",
			role=User.Role.FACULTY,
		)
		faculty_role = Role.objects.get(role_code=User.Role.FACULTY)
		UserRole.objects.get_or_create(user=user, role=faculty_role)

		response = self.client.patch(
			f"/api/admin/users/{user.pk}/roles/",
			{"roles": ["FACULTY", "LIBRARIAN"]},
			format="json",
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(set(response.data["roles"]), {"FACULTY", "LIBRARIAN"})

		response = self.client.post(
			f"/api/admin/users/{user.pk}/reset-password/",
			{"new_password": "NewPass123"},
			format="json",
		)
		self.assertEqual(response.status_code, 200)
		user.refresh_from_db()
		self.assertTrue(user.check_password("NewPass123"))

	def test_non_admin_cannot_use_admin_api(self):
		user = User.objects.create_user(
			username="faculty",
			email="faculty@example.com",
			password="TempPass123",
			role=User.Role.FACULTY,
		)
		self.client.force_authenticate(user)
		response = self.client.get("/api/admin/users/")
		self.assertEqual(response.status_code, 403)


class FacultyScopedApiTests(APITestCase):
	def setUp(self):
		self.faculty_user = User.objects.create_user(
			username="faculty1",
			email="faculty1@example.com",
			password="FacultyPass123",
			role=User.Role.FACULTY,
		)
		faculty_role = Role.objects.get(role_code=User.Role.FACULTY)
		UserRole.objects.get_or_create(user=self.faculty_user, role=faculty_role)
		self.faculty = self.faculty_user.employee.faculty_profile

		self.other_faculty_user = User.objects.create_user(
			username="faculty2",
			email="faculty2@example.com",
			password="FacultyPass123",
			role=User.Role.FACULTY,
		)
		UserRole.objects.get_or_create(user=self.other_faculty_user, role=faculty_role)

		department = __import__("academics.models", fromlist=["Department"]).Department.objects.create(
			department_code="IT", department_name="Information Technology"
		)
		program = Program.objects.create(program_code="BTECH-IT", program_name="B.Tech IT", department=department)
		year = AcademicYear.objects.create(year_code="2026-27", start_date="2026-06-01", end_date="2027-05-31")
		semester = Semester.objects.create(program=program, semester_number=5, name="Semester 5")
		course = Course.objects.create(department=department, name="IT", code="IT-COURSE")
		subject = Subject.objects.create(course=course, subject_code="DBMS", subject_name="Database Systems")
		self.section = Section.objects.create(
			program=program, semester=semester, academic_year=year, section_code="IT-B"
		)
		self.assignment = FacultySubject.objects.create(
			faculty=self.faculty, subject=subject, academic_year=year, semester=semester, section=self.section
		)
		self.student_user = User.objects.create_user(
			username="student1", email="student1@example.com", password="StudentPass123", role=User.Role.STUDENT
		)
		student_role = Role.objects.get(role_code=User.Role.STUDENT)
		UserRole.objects.get_or_create(user=self.student_user, role=student_role)
		SectionStudent.objects.create(section=self.section, student=self.student_user.student_profile)
		self.client.force_authenticate(self.faculty_user)

	def test_faculty_can_view_assignments_and_mark_attendance(self):
		response = self.client.get("/api/faculty/subjects/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["results"][0]["subject_code"], "DBMS")

		response = self.client.post(
			"/api/faculty/attendance/",
			{
				"subject": self.assignment.subject_id,
				"section": self.section.section_id,
				"academic_year": self.assignment.academic_year_id,
				"semester": self.assignment.semester_id,
				"attendance_date": "2026-09-24",
				"start_time": "09:00",
				"end_time": "10:00",
				"records": [{"student": self.student_user.student_profile.student_id, "status": "PRESENT"}],
			},
			format="json",
		)
		self.assertEqual(response.status_code, 201)

	def test_unassigned_faculty_cannot_mark_attendance(self):
		self.client.force_authenticate(self.other_faculty_user)
		response = self.client.post(
			"/api/faculty/attendance/",
			{
				"subject": self.assignment.subject_id,
				"section": self.section.section_id,
				"attendance_date": "2026-09-24",
				"start_time": "09:00",
				"end_time": "10:00",
				"records": [],
			},
			format="json",
		)
		self.assertEqual(response.status_code, 403)

	def test_faculty_can_update_limited_profile_and_submit_leave(self):
		response = self.client.patch(
			"/api/faculty/profile/",
			{
				"phone": "9999999999",
				"profile_photo": "https://example.com/faculty.jpg",
				"address": {
					"address_line1": "College Road",
					"city": "Pune",
					"state": "Maharashtra",
					"country": "India",
					"postal_code": "411001",
				},
			},
			format="json",
		)
		self.assertEqual(response.status_code, 200)
		self.faculty_user.refresh_from_db()
		self.assertEqual(self.faculty_user.phone, "9999999999")
		self.assertEqual(self.faculty_user.person.addresses.get(address_type="HOME").address.city, "Pune")
		leave_type = LeaveType.objects.create(name="Casual Leave", max_days=10)
		response = self.client.post(
			"/api/faculty/leave-requests/",
			{"leave_type": leave_type.pk, "start_date": "2026-10-10", "end_date": "2026-10-11", "reason": "Personal"},
			format="json",
		)
		self.assertEqual(response.status_code, 201)

	def test_faculty_can_enter_marks_for_assigned_students(self):
		exam_type = ExamType.objects.create(name="Internal")
		exam = Exam.objects.create(
			exam_type=exam_type, academic_year=self.assignment.academic_year,
			semester=self.assignment.semester, exam_name="Mid Semester",
			start_date="2026-09-20", end_date="2026-09-25",
		)
		exam_subject = ExamSubject.objects.create(
			exam=exam, subject=self.assignment.subject, exam_date="2026-09-24", max_marks=100, passing_marks=40
		)
		response = self.client.post(
			"/api/faculty/marks/",
			{"exam_subject": exam_subject.pk, "student": self.student_user.student_profile.student_id, "marks_obtained": 82},
			format="json",
		)
		self.assertEqual(response.status_code, 201)


class StudentSelfServiceApiTests(APITestCase):
	def setUp(self):
		self.student_user = User.objects.create_user(
			username="student-self", email="student-self@example.com", password="StudentPass123", role=User.Role.STUDENT
		)
		student_role = Role.objects.get(role_code=User.Role.STUDENT)
		UserRole.objects.get_or_create(user=self.student_user, role=student_role)
		self.other_user = User.objects.create_user(
			username="student-other", email="student-other@example.com", password="StudentPass123", role=User.Role.STUDENT
		)
		UserRole.objects.get_or_create(user=self.other_user, role=student_role)

		from academics.models import Department
		department = Department.objects.create(department_code="STU", department_name="Student Department")
		program = Program.objects.create(program_code="BCA", program_name="BCA", department=department)
		year = AcademicYear.objects.create(year_code="2026-28", start_date="2026-06-01", end_date="2028-05-31")
		semester = Semester.objects.create(program=program, semester_number=1, name="Semester 1")
		course = Course.objects.create(department=department, name="BCA Course", code="BCA-COURSE")
		subject = Subject.objects.create(course=course, subject_code="PY", subject_name="Python")
		ProgramSubject.objects.create(program=program, semester=semester, subject=subject)
		self.section = Section.objects.create(program=program, semester=semester, academic_year=year, section_code="A")
		for profile in (self.student_user.student_profile, self.other_user.student_profile):
			profile.program = program
			profile.department = department
			profile.current_semester = 1
			profile.save(update_fields=("program", "department", "current_semester"))
			SectionStudent.objects.create(section=self.section, student=profile)
		self.session = AttendanceSession.objects.create(
			subject=subject, faculty=User.objects.create_user(username="teacher", email="teacher@example.com", role=User.Role.FACULTY).employee.faculty_profile,
			section=self.section, attendance_date="2026-09-24", start_time="09:00", end_time="10:00"
		)
		StudentAttendance.objects.create(attendance_session=self.session, student=self.student_user.student_profile, status="PRESENT")
		StudentAttendance.objects.create(attendance_session=self.session, student=self.other_user.student_profile, status="ABSENT")
		self.fee_account = StudentFeeAccount.objects.create(student=self.student_user.student_profile, academic_year=year, total_amount=1000, pending_amount=1000)
		category = FeeCategory.objects.create(category_code="TUITION", category_name="Tuition")
		self.invoice = FeeInvoice.objects.create(fee_account=self.fee_account, invoice_number="INV-STUDENT-1", invoice_date="2026-09-01", due_date="2026-10-01", total_amount=1000)
		self.client.force_authenticate(self.student_user)

	def test_student_reads_only_own_attendance_even_with_foreign_query_id(self):
		response = self.client.get(f"/api/student/attendance/?student_id={self.other_user.student_profile.student_id}")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["total"], 1)
		self.assertEqual(response.data["history"][0]["status"], "PRESENT")

	def test_student_can_update_allowed_profile_fields_only(self):
		response = self.client.patch(
			"/api/student/profile/",
			{"phone": "8888888888", "emergency_contact": "7777777777", "address": {"address_line1": "Main Road", "city": "Pune", "state": "Maharashtra", "postal_code": "411001"}},
			format="json",
		)
		self.assertEqual(response.status_code, 200)
		self.student_user.refresh_from_db()
		self.assertEqual(self.student_user.phone, "8888888888")
		self.assertEqual(self.student_user.student_profile.current_semester, 1)

	def test_student_payment_amount_is_derived_from_invoice(self):
		response = self.client.post("/api/student/fees/payments/", {"invoice": self.invoice.invoice_id, "amount": 1}, format="json")
		self.assertEqual(response.status_code, 201)
		self.assertEqual(str(response.data["amount"]), "1000.00")

	def test_student_can_submit_request_but_cannot_mark_attendance(self):
		response = self.client.post(
			"/api/student/requests/",
			{"request_type": "BONAFIDE", "description": "Please issue a bonafide certificate."},
			format="json",
		)
		self.assertEqual(response.status_code, 201)
		response = self.client.post("/api/attendance/", {}, format="json")
		self.assertEqual(response.status_code, 403)


class AdminAcademicAssignmentTests(APITestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username="academic-admin", email="academic-admin@example.com", password="AdminPass123", role=User.Role.ADMIN
		)
		admin_role = Role.objects.get(role_code=User.Role.ADMIN)
		UserRole.objects.get_or_create(user=self.admin, role=admin_role)
		self.faculty_user = User.objects.create_user(
			username="assigned-faculty", email="assigned-faculty@example.com", password="FacultyPass123", role=User.Role.FACULTY
		)
		faculty_role = Role.objects.get(role_code=User.Role.FACULTY)
		UserRole.objects.get_or_create(user=self.faculty_user, role=faculty_role)
		self.student = User.objects.create_user(
			username="placed-student", email="placed-student@example.com", password="StudentPass123", role=User.Role.STUDENT
		).student_profile
		student_role = Role.objects.get(role_code=User.Role.STUDENT)
		UserRole.objects.get_or_create(user=self.student.user, role=student_role)

		from academics.models import Department
		department = Department.objects.create(department_code="CSE", department_name="Computer Science")
		program = Program.objects.create(program_code="BTECH-CSE", program_name="B.Tech CSE", department=department)
		year = AcademicYear.objects.create(year_code="2026-29", start_date="2026-06-01", end_date="2029-05-31")
		semester = Semester.objects.create(program=program, semester_number=3, name="Semester 3")
		course = Course.objects.create(department=department, name="CSE Course", code="CSE-COURSE")
		subject = Subject.objects.create(course=course, subject_code="DSA", subject_name="Data Structures")
		ProgramSubject.objects.create(program=program, semester=semester, subject=subject)
		self.section = Section.objects.create(program=program, semester=semester, academic_year=year, section_code="CSE-A")
		self.payload = {
			"program": program.pk,
			"department": department.pk,
			"semester": semester.pk,
			"section": self.section.pk,
			"academic_year": year.pk,
			"roll_number": "23",
		}

	def test_admin_assigns_student_and_faculty_class(self):
		self.client.force_authenticate(self.admin)
		response = self.client.patch(f"/api/admin/students/{self.student.pk}/academic/", self.payload, format="json")
		self.assertEqual(response.status_code, 200)
		self.student.refresh_from_db()
		self.assertEqual(self.student.program_id, self.payload["program"])
		self.assertEqual(self.student.current_semester, 3)
		self.assertTrue(self.section.students.filter(pk=self.student.pk).exists())

		response = self.client.post(
			"/api/admin/faculty-assignments/",
			{
				"faculty": self.faculty_user.employee.faculty_profile.pk,
				"subject": self.section.program.program_subjects.first().subject_id,
				"academic_year": self.section.academic_year_id,
				"semester": self.section.semester_id,
				"section": self.section.pk,
			},
			format="json",
		)
		self.assertEqual(response.status_code, 201)

		self.client.force_authenticate(self.faculty_user)
		response = self.client.get(f"/api/faculty/sections/{self.section.pk}/students/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data[0]["student_id"], self.student.pk)

	def test_student_cannot_change_academic_placement(self):
		self.client.force_authenticate(self.student.user)
		response = self.client.patch(f"/api/admin/students/{self.student.pk}/academic/", self.payload, format="json")
		self.assertEqual(response.status_code, 403)

	def test_admin_can_create_department(self):
		self.client.force_authenticate(self.admin)
		response = self.client.post(
			"/api/admin/departments/",
			{"department_code": "ECE", "department_name": "Electronics and Communication"},
			format="json",
		)
		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["department_code"], "ECE")
		duplicate = self.client.post(
			"/api/admin/departments/",
			{"department_code": "ece", "department_name": "Another Electronics Department"},
			format="json",
		)
		self.assertEqual(duplicate.status_code, 400)

	def test_admin_can_create_program_with_eight_semesters_and_courses(self):
		self.client.force_authenticate(self.admin)
		from academics.models import Department, ProgramSubject, Semester
		department = Department.objects.get(department_name="Computer Science")
		semesters = [
			{
				"semester_number": number,
				"courses": [{"code": f"CS{number:02d}01", "name": f"Computer Science Course {number}", "credits": 4}],
			}
			for number in range(1, 9)
		]
		response = self.client.post(
			"/api/admin/programs/",
			{
				"program_code": "BTECH-CS",
				"program_name": "B.Tech Computer Science",
				"department": department.pk,
				"degree_type": "B.Tech",
				"duration_years": 4,
				"semesters": semesters,
			},
			format="json",
		)
		self.assertEqual(response.status_code, 201)
		self.assertEqual(len(response.data["semesters"]), 8)
		program = Program.objects.get(program_code="BTECH-CS")
		self.assertEqual(program.semesters.count(), 8)
		self.assertEqual(ProgramSubject.objects.filter(program=program).count(), 8)
