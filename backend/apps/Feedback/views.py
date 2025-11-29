from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser

from .serializers import FeedbackSerializer
from .models import Feedback


class FeedbackCreateAPIView(APIView):
    """
    Public endpoint for submitting feedback.
    Allows GET (to avoid 405 errors) and POST (to submit feedback).
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {"detail": "Use POST to submit feedback."},
            status=status.HTTP_200_OK
        )

    def post(self, request):
        print(f"POST /api/feedback/ - received data: {request.data}")
        serializer = FeedbackSerializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        feedback = serializer.save()
        return Response(
            FeedbackSerializer(feedback).data,
            status=status.HTTP_201_CREATED
        )


class FeedbackListAPIView(APIView):
    """Admin-only list view for feedback entries."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        queryset = Feedback.objects.all().order_by("-created_at")
        serializer = FeedbackSerializer(queryset, many=True)
        return Response(serializer.data)
