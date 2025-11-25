from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import FacultyFeedbackMessage
from .serializers import FacultyFeedbackMessageSerializer


class FacultySendFeedbackAPIView(generics.CreateAPIView):
    serializer_class = FacultyFeedbackMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class StudentFeedbackListAPIView(generics.ListAPIView):
    serializer_class = FacultyFeedbackMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FacultyFeedbackMessage.objects.filter(
            receiver=self.request.user
        )


class MarkMessageReadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            msg = FacultyFeedbackMessage.objects.get(id=pk, receiver=request.user)
            msg.is_read = True
            msg.save()
            return Response({"detail": "Message marked as read"})
        except FacultyFeedbackMessage.DoesNotExist:
            return Response({"detail": "Message not found"}, status=404)