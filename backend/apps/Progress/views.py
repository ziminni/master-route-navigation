from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404

from .models import FacultyFeedbackMessage
from .serializers import FacultyFeedbackMessageSerializer


class FacultySendFeedbackAPIView(generics.CreateAPIView):
    serializer_class = FacultyFeedbackMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        serializer.save(faculty=self.request.user)


class StudentFeedbackListAPIView(generics.ListAPIView):
    serializer_class = FacultyFeedbackMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return FacultyFeedbackMessage.objects.filter(
            student=self.request.user
        ).order_by("-date_sent")


class MarkMessageReadAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        msg = get_object_or_404(FacultyFeedbackMessage, pk=pk)
        if msg.student != request.user:
            return Response({"detail": "Not allowed"}, status=403)
        msg.status = "read"
        msg.save(update_fields=["status"])
        return Response({"detail": "Message marked as read"})


class DeleteMessageAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        msg = get_object_or_404(FacultyFeedbackMessage, pk=pk)
        if msg.student != request.user:
            return Response({"detail": "Not allowed"}, status=403)
        msg.delete()
        return Response({"detail": "Deleted successfully"}, status=204)


class FacultySendSingleNoteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if getattr(request.user, "role_type", "") != "faculty":
            return Response({"detail": "Forbidden"}, status=403)

        student_id = request.data.get("student_id")
        notes = request.data.get("notes", "")

        if not student_id:
            return Response({"detail": "student_id required"}, status=400)

        from apps.Users.models import StudentProfile
        student = get_object_or_404(StudentProfile, user__id=student_id)
        student.faculty_notes = notes
        student.save(update_fields=["faculty_notes"])
        return Response({"notes": notes}, status=200)
