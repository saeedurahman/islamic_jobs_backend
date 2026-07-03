from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import PublicProfileFilter
from .models import Profile
from .permissions import IsJobSeeker
from .serializers import (
    ProfileListSerializer,
    ProfileOwnerSerializer,
    ProfilePublicSerializer,
)

PROFILE_RELATED_PREFETCH = (
    'hifz_records',
    'dars_nizami_records',
    'mufti_course_records',
    'ijazah_records',
    'nazra_qirat_records',
    'asri_education_records',
    'languages',
    'skills',
)


class MeProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsJobSeeker]
    serializer_class = ProfileOwnerSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        try:
            return (
                Profile.objects.prefetch_related(*PROFILE_RELATED_PREFETCH)
                .get(user=self.request.user)
            )
        except Profile.DoesNotExist:
            raise NotFound('Job seeker profile not found.')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        return Response(self.get_serializer(instance).data)


class ProfileListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProfileListSerializer
    filterset_class = PublicProfileFilter

    def get_queryset(self):
        return (
            Profile.objects.filter(
                is_public=True,
                verification_status=Profile.VerificationStatus.VERIFIED,
            )
            .select_related('province', 'city')
            .prefetch_related('hifz_records', 'dars_nizami_records')
            .order_by('-created_at')
        )


class ProfileDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProfilePublicSerializer

    def get_queryset(self):
        return Profile.objects.select_related(
            'province', 'city', 'district', 'village'
        ).prefetch_related(*PROFILE_RELATED_PREFETCH)

    def get_object(self):
        profile = get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        if not profile.is_visible_publicly():
            raise NotFound()
        return profile
