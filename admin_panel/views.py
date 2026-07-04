from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsAdminUser
from applications.models import Application
from employers.models import Employer
from jobs.models import JobPosting
from profiles.models import Profile

from .filters import AdminEmployerFilter, AdminJobFilter, AdminProfileFilter, AdminUserFilter
from .serializers import (
    AdminCreateEmployerAndJobResponseSerializer,
    AdminCreateEmployerAndJobSerializer,
    AdminEmployerDetailSerializer,
    AdminEmployerListSerializer,
    AdminJobListSerializer,
    AdminProfileDetailSerializer,
    AdminProfileListSerializer,
    AdminUserListSerializer,
    VerificationStatusSerializer,
)

PROFILE_DETAIL_SELECT_RELATED = (
    'user', 'province', 'city', 'district', 'village',
)
PROFILE_DETAIL_PREFETCH = (
    'hifz_records',
    'dars_nizami_records',
    'mufti_course_records',
    'ijazah_records',
    'nazra_qirat_records',
    'asri_education_records',
    'languages',
    'skills',
)

EMPLOYER_DETAIL_SELECT_RELATED = (
    'user', 'province', 'city', 'district', 'village',
)


class AdminProfileListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminProfileListSerializer
    filterset_class = AdminProfileFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        return (
            Profile.objects.select_related('user', 'province', 'city')
            .order_by('-created_at')
        )


class AdminProfileVerifyView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        profile = get_object_or_404(Profile, pk=pk)
        serializer = VerificationStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        if profile.verification_status == new_status:
            label = 'verified' if new_status == 'verified' else 'rejected'
            return Response(
                {'detail': f'Profile is already {label}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.verification_status = new_status
        profile.save(update_fields=['verification_status'])
        output = AdminProfileListSerializer(profile, context={'request': request})
        return Response(output.data)


class AdminProfileDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminProfileDetailSerializer

    def get_queryset(self):
        return (
            Profile.objects.select_related(*PROFILE_DETAIL_SELECT_RELATED)
            .prefetch_related(*PROFILE_DETAIL_PREFETCH)
        )


class AdminProfileDisableView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        profile = get_object_or_404(
            Profile.objects.select_related('user', 'province', 'city'),
            pk=pk,
        )
        if profile.is_disabled:
            return Response(
                {'detail': 'Profile is already disabled.', 'is_disabled': True},
                status=status.HTTP_200_OK,
            )

        profile.is_disabled = True
        profile.save(update_fields=['is_disabled'])
        output = AdminProfileListSerializer(profile, context={'request': request})
        return Response({'detail': 'Profile disabled.', 'profile': output.data})


class AdminProfileEnableView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        profile = get_object_or_404(
            Profile.objects.select_related('user', 'province', 'city'),
            pk=pk,
        )
        if not profile.is_disabled:
            return Response(
                {'detail': 'Profile is already enabled.', 'is_disabled': False},
                status=status.HTTP_200_OK,
            )

        profile.is_disabled = False
        profile.save(update_fields=['is_disabled'])
        output = AdminProfileListSerializer(profile, context={'request': request})
        return Response({'detail': 'Profile enabled.', 'profile': output.data})


class AdminEmployerListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminEmployerListSerializer
    filterset_class = AdminEmployerFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        return (
            Employer.objects.select_related('user', 'province', 'city')
            .order_by('-created_at')
        )


class AdminEmployerVerifyView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        employer = get_object_or_404(Employer, pk=pk)
        serializer = VerificationStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        if employer.verification_status == new_status:
            label = 'verified' if new_status == 'verified' else 'rejected'
            return Response(
                {'detail': f'Employer is already {label}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employer.verification_status = new_status
        employer.save(update_fields=['verification_status'])
        output = AdminEmployerListSerializer(employer, context={'request': request})
        return Response(output.data)


class AdminEmployerDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminEmployerDetailSerializer

    def get_queryset(self):
        return Employer.objects.select_related(*EMPLOYER_DETAIL_SELECT_RELATED)


class AdminJobListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminJobListSerializer
    filterset_class = AdminJobFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        return (
            JobPosting.objects.select_related('employer')
            .order_by('-created_at')
        )


class AdminJobRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        job = get_object_or_404(JobPosting.objects.select_related('employer'), pk=pk)
        if job.status == JobPosting.Status.REMOVED:
            return Response(
                {'detail': 'Job is already removed.', 'status': job.status},
                status=status.HTTP_200_OK,
            )

        job.status = JobPosting.Status.REMOVED
        job.save(update_fields=['status'])
        output = AdminJobListSerializer(job, context={'request': request})
        return Response(
            {
                'detail': 'Job removed from public view.',
                'job': output.data,
            }
        )


class AdminJobHardDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, pk):
        job = get_object_or_404(JobPosting, pk=pk)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminUserListSerializer
    filterset_class = AdminUserFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        return User.objects.order_by('-created_at')


class AdminUserHardDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.pk == request.user.pk:
            return Response(
                {'detail': 'You cannot delete your own admin account.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.user_role == User.Role.ADMIN:
            return Response(
                {'detail': 'Admin accounts cannot be deleted from this endpoint.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        now = timezone.now()
        data = {
            'total_job_seekers': User.objects.filter(user_role=User.Role.JOB_SEEKER).count(),
            'total_employers': User.objects.filter(user_role=User.Role.EMPLOYER).count(),
            'total_active_jobs': JobPosting.objects.filter(
                status=JobPosting.Status.ACTIVE,
            ).filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=now),
            ).count(),
            'total_applications': Application.objects.count(),
            'pending_profile_verifications': Profile.objects.filter(
                verification_status=Profile.VerificationStatus.PENDING,
            ).count(),
            'pending_employer_verifications': Employer.objects.filter(
                verification_status=Employer.VerificationStatus.PENDING,
            ).count(),
        }
        return Response(data)


class AdminCreateEmployerAndJobView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = AdminCreateEmployerAndJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        output = AdminCreateEmployerAndJobResponseSerializer(
            result,
            context={'request': request},
        )
        return Response(output.data, status=status.HTTP_201_CREATED)
