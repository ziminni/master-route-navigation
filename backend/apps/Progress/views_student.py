# backend/apps/Progress/views_student.py
from collections import defaultdict
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.Users.models import StudentProfile
from apps.Progress.models import FinalGrade, FacultyFeedbackMessage, ClassScheduleInfo
from apps.Academics.models import Enrollment, Semester


# ----------------------------
# Helpers: semester normalization
# ----------------------------
def _normalize_term(term):
    """
    Normalize various representations of semester/term into canonical 'first' or 'second'.
    Accepts strings like: 'first', '1st', '1', 'First Semester', 'second', '2nd', '2', integer 1/2.
    Returns 'first' or 'second' or original lowercased string fallback.
    """
    if term is None:
        return None
    # handle numbers
    try:
        if isinstance(term, (int, float)):
            if int(term) == 1:
                return "first"
            if int(term) == 2:
                return "second"
    except Exception:
        pass

    t = str(term).strip().lower()
    # common matches
    if t in ("1", "1st", "first", "first sem", "1st sem", "first semester", "1st semester"):
        return "first"
    if t in ("2", "2nd", "second", "second sem", "2nd sem", "second semester", "2nd semester"):
        return "second"
    # fallback: if contains 'first' or '1' etc
    if "first" in t or t.startswith("1"):
        return "first"
    if "second" in t or t.startswith("2"):
        return "second"
    # unknown: return raw lowercased (safe fallback)
    return t


def _canonical_semester_label(semester_obj):
    """
    Build canonical label used by frontend: "2024-2025 – first"
    Works even if semester_obj fields vary.
    """
    if not semester_obj:
        return "unknown"

    ay = getattr(semester_obj, "academic_year", "") or ""
    term_raw = getattr(semester_obj, "term", "")
    term = _normalize_term(term_raw) or str(term_raw).strip().lower()
    if ay and term:
        return f"{ay} – {term}"
    if ay:
        return ay
    return str(term)


def _parse_semester_param(param):
    """
    Turn a semester query param into (academic_year, normalized_term).
    Accepts inputs like:
      - "2024-2025 – first"
      - "2024-2025 first"
      - "2024-2025 1st Sem"
      - "2024-2025 - first"
      - "first" (term only)
    Returns tuple (academic_year_or_None, normalized_term_or_None)
    """
    if not param:
        return None, None
    p = str(param).strip()
    # normalize dashes
    p = p.replace("—", " - ").replace("–", " - ").replace("—", " - ").replace("−", " - ")
    parts = [seg.strip() for seg in p.split("-") if seg.strip()]
    # if it was "2024-2025 – first" after replacement might be ["2024", "2025", "first"] or ["2024-2025", "first"]
    if len(parts) == 1:
        # maybe "2024-2025 first" (space separated)
        sp = parts[0].split()
        if len(sp) >= 2:
            ay_candidate = sp[0]
            term_candidate = " ".join(sp[1:])
            return ay_candidate, _normalize_term(term_candidate)
        # single token: could be year or term
        token = parts[0]
        if token.count("20") >= 1 and ("-" in token or token.count("/") >= 1):
            # treat as academic year
            return token, None
        # treat as term only
        return None, _normalize_term(token)
    # if last part looks like term
    ay = None
    term = None
    # try to find academic_year in parts
    # combine first two if they look like "2024 2025" or "2024-2025"
    if len(parts) >= 2:
        # try combine first two
        candidate_ay = parts[0]
        # if candidate_ay doesn't contain a dash but next part looks numeric, join them
        if "-" not in candidate_ay and len(parts) >= 2 and any(ch.isdigit() for ch in parts[1]):
            candidate_ay = f"{parts[0]}-{parts[1]}"
            # then term might be parts[2] if exists
            if len(parts) >= 3:
                term = _normalize_term(parts[2])
            else:
                term = None
            ay = candidate_ay
            return ay, term
        # otherwise assume parts[0] is ay and last part is term
        ay = parts[0]
        term = _normalize_term(parts[-1])
        return ay, term

    return None, None


# ----------------------------
# Helpers: grade computation
# ----------------------------
def _to_float_safe(val):
    try:
        return float(str(val))
    except Exception:
        return None


def _compute_numeric_grade(final_grade_obj):
    """
    Compute numeric grade used for GWA:
    - If re_exam exists and parseable -> use re_exam
    - Else if both midterm and finals available -> average(midterm, finals)
    - Else fallback to final_grade
    - Return None if nothing parseable
    """
    if not final_grade_obj:
        return None

    # re-exam field name may vary: try common names
    re_exam_val = None
    for attr in ("re_exam", "re_exam_grade", "reexam", "reexam_grade"):
        if hasattr(final_grade_obj, attr):
            re_exam_val = getattr(final_grade_obj, attr)
            if re_exam_val not in (None, "", []):
                v = _to_float_safe(re_exam_val)
                if v is not None:
                    return v
            break

    # average midterm + finals if both available
    m = _to_float_safe(getattr(final_grade_obj, "midterm_grade", None) or getattr(final_grade_obj, "midterm", None))
    f = _to_float_safe(getattr(final_grade_obj, "final_term_grade", None) or getattr(final_grade_obj, "finals", None) or getattr(final_grade_obj, "final_grade", None))
    if m is not None and f is not None:
        return (m + f) / 2.0

    # fallback to stored final_grade
    fg = _to_float_safe(getattr(final_grade_obj, "final_grade", None))
    return fg


# ----------------------------
# Degree Progress Calculation
# ----------------------------
def calculate_student_progress_for_api(user):
    """Calculate degree progress for student API views"""
    try:
        # Get all final grades for this student
        final_grades = FinalGrade.objects.filter(student=user).select_related('course')
        total_courses = final_grades.count()
        
        if total_courses == 0:
            return {
                "General Education": 0,
                "Major": 0,
                "Electives": 0
            }
        
        # Initialize counters
        major_count = 0
        elective_count = 0
        ge_count = 0
        
        # Categorize passed courses
        for grade in final_grades:
            if grade.status.lower() == "passed" and grade.course:
                course_code = grade.course.code.upper() if grade.course.code else ""
                course_title = grade.course.title.upper() if grade.course.title else ""
                
                # Categorize based on course code/title patterns
                if "GE" in course_code or "GENERAL" in course_title or "LIBERAL" in course_title:
                    ge_count += 1
                elif "ELECT" in course_code or "ELECTIVE" in course_title or "OPTIONAL" in course_title:
                    elective_count += 1
                else:
                    major_count += 1
        
        # Calculate percentages based on typical requirements
        # These should match the category_totals below
        requirements = {
            "General Education": 20,
            "Major": 40,
            "Electives": 10
        }
        
        progress = {
            "General Education": min(100, int((ge_count / requirements["General Education"]) * 100)) if requirements["General Education"] > 0 else 0,
            "Major": min(100, int((major_count / requirements["Major"]) * 100)) if requirements["Major"] > 0 else 0,
            "Electives": min(100, int((elective_count / requirements["Electives"]) * 100)) if requirements["Electives"] > 0 else 0
        }
        
        return progress
    except Exception as e:
        print(f"DEBUG: Error calculating student progress: {e}")
        # Fallback to reasonable defaults
        return {
            "General Education": 25,
            "Major": 25,
            "Electives": 25
        }


# ----------------------------
# API Views
# ----------------------------
class StudentGradesAPIView(APIView):
    """
    Returns FinalGrade grouped by academic years & semesters in the exact string format
    the frontend dropdown uses: '2024-2025 – first'
    Each course entry includes a 'computed_grade' used by GWA calculations.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # ensure user is student
        try:
            StudentProfile.objects.get(user=user)
        except StudentProfile.DoesNotExist:
            return Response({"academic_years": []}, status=200)

        grades_qs = FinalGrade.objects.filter(student=user).select_related("semester", "course")
        if not grades_qs.exists():
            return Response({"academic_years": []}, status=200)

        # Build mapping year -> semesters -> courses (matching frontend expected structure)
        year_map = {}
        for g in grades_qs:
            sem = getattr(g, "semester", None)
            ay = getattr(sem, "academic_year", "") if sem else ""
            term_norm = _normalize_term(getattr(sem, "term", None)) if sem else ""
            sem_key = f"{ay} – {term_norm}" if ay and term_norm else (ay or term_norm or "unknown")

            computed = _compute_numeric_grade(g)
            computed_str = "" if computed is None else ("{:.2f}".format(computed))

            # prepare course payload
            course_obj = getattr(g, "course", None)
            course_payload = {
                "subject_code": getattr(course_obj, "code", "") if course_obj else "",
                "description": getattr(course_obj, "title", "") if course_obj else "",
                "units": getattr(course_obj, "units", 0) if course_obj else 0,
                "midterm": getattr(g, "midterm_grade", "") or getattr(g, "midterm", ""),
                "finals": getattr(g, "final_term_grade", "") or getattr(g, "finals", "") or getattr(g, "final_grade", ""),
                "re_exam": getattr(g, "re_exam", "") if hasattr(g, "re_exam") else (getattr(g, "re_exam_grade", "") if hasattr(g, "re_exam_grade") else ""),
                "remarks": (getattr(g, "status", "") or "").capitalize(),
                "computed_grade": computed_str,
            }

            # insert into year_map
            if ay not in year_map:
                year_map[ay] = {"school_year": ay, "semesters": {}}
            sems = year_map[ay]["semesters"]
            if sem_key not in sems:
                sems[sem_key] = {"name": term_norm, "courses": []}
            sems[sem_key]["courses"].append(course_payload)

        # convert sems mapping into list format expected by frontend
        academic_years = []
        for ay, info in year_map.items():
            sems_list = []
            for sem_key, sem_info in info["semesters"].items():
                sems_list.append({"name": sem_info["name"], "courses": sem_info["courses"]})
            academic_years.append({"school_year": ay, "semesters": sems_list})

        return Response({"academic_years": academic_years}, status=200)


class StudentGWAAPIView(APIView):
    """
    Returns numeric GWA data per semester. Uses 'computed_grade' logic:
    - if re-exam exists -> use re-exam value
    - else average(midterm, finals)
    - else final_grade
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            StudentProfile.objects.get(user=user)
        except StudentProfile.DoesNotExist:
            return Response({"semesters": {}}, status=200)

        grades_qs = FinalGrade.objects.filter(student=user).select_related("semester", "course")
        sem_map = {}

        for g in grades_qs:
            sem_obj = getattr(g, "semester", None)
            sem_key = _canonical_semester_label(sem_obj)
            numeric = _compute_numeric_grade(g)
            if numeric is None:
                continue
            if sem_key not in sem_map:
                sem_map[sem_key] = {"numbers": [], "units": 0}
            sem_map[sem_key]["numbers"].append(numeric)
            # optionally include units if you want weighted GWA; for now we bundle units too
            try:
                units = int(getattr(g.course, "units", 0))
            except Exception:
                units = 0
            sem_map[sem_key]["units"] += units

        # compute gwa per semester (simple average of computed grades)
        out = {}
        for sem_key, info in sem_map.items():
            nums = info["numbers"]
            if not nums:
                out[sem_key] = None
            else:
                out[sem_key] = round(sum(nums) / len(nums), 3)

        return Response({"semesters": out}, status=200)


class StudentSubjectsAPIView(APIView):
    """
    Returns enrolled classes grouped by canonical semester label.
    Each subject entry includes schedule, room, instructor, and re_exam.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        subjects_grouped = {}

        enrollments = Enrollment.objects.filter(student__user=user).select_related(
            "enrolled_class",
            "enrolled_class__course",
            "enrolled_class__semester",
            "enrolled_class__faculty",
            "enrolled_class__faculty__user"
        ).prefetch_related('enrolled_class__schedule_info')

        for e in enrollments:
            clazz = e.enrolled_class
            if not clazz:
                continue
            course = clazz.course
            sem_obj = clazz.semester
            sem_label = _canonical_semester_label(sem_obj)

            fg = FinalGrade.objects.filter(student=user, course=course, semester=sem_obj).first()
            
            # Get schedule info from ClassScheduleInfo model or fallback to Class model
            schedule = ""
            room = ""
            
            # Try to get from ClassScheduleInfo first
            try:
                schedule_info = getattr(clazz, 'schedule_info', None)
                if schedule_info:
                    schedule = schedule_info.schedule
                    room = schedule_info.room
            except:
                pass
            
            # Fallback to Class model fields if schedule_info not available
            if not schedule and hasattr(clazz, 'schedule'):
                schedule = getattr(clazz, 'schedule', '')
            if not room and hasattr(clazz, 'room'):
                room = getattr(clazz, 'room', '')

            if sem_label not in subjects_grouped:
                subjects_grouped[sem_label] = {"subjects": []}

            subjects_grouped[sem_label]["subjects"].append({
                "subject_code": getattr(course, "code", "") if course else "",
                "description": getattr(course, "title", "") if course else "",
                "units": getattr(course, "units", 0) if course else 0,
                "schedule": schedule,
                "room": room,
                "instructor": (clazz.faculty.user.get_full_name() if getattr(clazz, "faculty", None) and hasattr(clazz.faculty, "user") else "") if getattr(clazz, "faculty", None) else "",
                "re_exam": (fg.re_exam if fg and getattr(fg, "re_exam", None) else (fg.re_exam_grade if fg and getattr(fg, "re_exam_grade", None) else "")) if fg else "",
            })

        return Response({"semesters": subjects_grouped}, status=200)


class StudentDegreeProgressAPIView(APIView):
    """
    Returns actual degree-progress payload grouped by canonical semester labels.
    Now calculates actual progress percentages instead of hardcoded values.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            StudentProfile.objects.get(user=user)
        except StudentProfile.DoesNotExist:
            return Response({}, status=200)

        grades_qs = FinalGrade.objects.filter(student=user).select_related("semester", "course").order_by("-semester__start_date")
        sems = {}
        for g in grades_qs:
            sem_obj = getattr(g, "semester", None)
            label = _canonical_semester_label(sem_obj)
            if label not in sems:
                sems[label] = {"subjects": []}

            sems[label]["subjects"].append({
                "no": "",
                "subject_code": getattr(g.course, "code", ""),
                "description": getattr(g.course, "title", ""),
                "units": getattr(g.course, "units", 0),
                "year_term": label,
                "grades": {
                    "midterm": g.midterm_grade,
                    "finals": g.final_term_grade,
                },
                "pre_requisites": ""
            })

        # Calculate actual progress
        progress_data = calculate_student_progress_for_api(user)
        
        response = {
            "category_totals": {
                "General Education": 20,
                "Major": 40,  # This is "Core Courses" in admin view
                "Electives": 10
            },
            "category_progress": progress_data,  # Add progress percentages
            "semesters": sems
        }
        return Response(response, status=200)


class StudentLatestNoteAPIView(APIView):
    """
    Return the latest faculty note for the student, optionally filtered to a specific semester.
    Accepts query param: semester (various formats)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        semester_param = request.query_params.get("semester")
        target_user = request.user

        qs = FacultyFeedbackMessage.objects.filter(student=target_user).select_related("grade", "grade__semester").order_by("-date_sent")
        if semester_param:
            ay, term = _parse_semester_param(semester_param)
            # If academic year provided, filter by it and normalized term (if present)
            if ay:
                if term:
                    qs = qs.filter(grade__semester__academic_year__iexact=ay, grade__semester__term__iexact=term)
                else:
                    qs = qs.filter(grade__semester__academic_year__iexact=ay)
            else:
                # No AY found; try to match by term only (normalized)
                if term:
                    # Loop to find first matching message where term matches normalized term
                    matched = None
                    for m in qs:
                        sem = getattr(m, "grade", None) and getattr(m.grade, "semester", None)
                        if sem:
                            sem_term = _normalize_term(getattr(sem, "term", None))
                            if sem_term == term:
                                matched = m
                                break
                    msg = matched
                    return Response({"notes": "" if not msg else (msg.message or "")}, status=200)

        msg = qs.first()
        return Response({"notes": "" if not msg else (msg.message or "")}, status=200)