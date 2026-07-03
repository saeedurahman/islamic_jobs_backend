from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Employer
from .permissions import IsEmployer
from .serializers import EmployerOwnerSerializer, EmployerPublicSerializer


class MeEmployerView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsEmployer]
    serializer_class = EmployerOwnerSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        try:
            return (
                Employer.objects.select_related('province', 'city', 'district', 'village')
                .get(user=self.request.user)
            )
        except Employer.DoesNotExist:
            raise NotFound('Employer profile not found.')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        return Response(self.get_serializer(instance).data)


class EmployerDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmployerPublicSerializer

    def get_queryset(self):
        return Employer.objects.select_related(
            'province', 'city', 'district', 'village'
        )

    def get_object(self):
        employer = get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        if not employer.is_visible_publicly():
            raise NotFound()
        return employer
