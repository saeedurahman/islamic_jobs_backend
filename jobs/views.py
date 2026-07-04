from django.db.models import BooleanField, Count, Exists, OuterRef, Q, Value
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from employers.permissions import IsEmployer
from profiles.models import Profile
from profiles.permissions import IsJobSeeker

from .filters import JobPostingFilter
from .models import JobPosting, SavedJob
from .pagination import JobPagination
from .permissions import IsJobOwner
from .serializers import JobListSerializer, JobOwnerSerializer, JobPublicSerializer

JOB_SELECT_RELATED = ('employer', 'employer__city', 'province', 'city', 'district')
JOB_PREFETCH = ('required_languages',)


def active_jobs_filter_qs():
    now = timezone.now()
    return JobPosting.objects.filter(status=JobPosting.Status.ACTIVE).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )


def active_jobs_queryset():
    return (
        active_jobs_filter_qs()
        .select_related(*JOB_SELECT_RELATED)
        .prefetch_related(*JOB_PREFETCH)
    )


def with_saved_status(queryset, user):
    if user.is_authenticated:
        return queryset.annotate(
            is_saved=Exists(
                SavedJob.objects.filter(user=user, job_id=OuterRef('pk'))
            )
        )
    return queryset.annotate(is_saved=Value(False, output_field=BooleanField()))


class JobListCreateView(generics.ListCreateAPIView):
    pagination_class = JobPagination
    filterset_class = JobPostingFilter
    filter_backends = [DjangoFilterBackend]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsEmployer()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobOwnerSerializer
        return JobListSerializer

    def get_queryset(self):
        return with_saved_status(active_jobs_queryset(), self.request.user)

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user.employer_profile)


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    lookup_url_kwarg = 'pk'
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsJobOwner()]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return JobPublicSerializer
        return JobOwnerSerializer

    def get_queryset(self):
        queryset = (
            JobPosting.objects.select_related(*JOB_SELECT_RELATED)
            .prefetch_related(*JOB_PREFETCH)
        )
        if self.request.method == 'GET':
            queryset = queryset.exclude(status=JobPosting.Status.REMOVED)
        return with_saved_status(queryset, self.request.user)


class SavedJobToggleView(APIView):
    permission_classes = [IsAuthenticated, IsJobSeeker]

    def post(self, request, pk):
        job = get_object_or_404(JobPosting, pk=pk)
        _, created = SavedJob.objects.get_or_create(user=request.user, job=job)
        if created:
            return Response(
                {'detail': 'Job saved.', 'is_saved': True},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {'detail': 'Job is already saved.', 'is_saved': True},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        deleted_count, _ = SavedJob.objects.filter(user=request.user, job_id=pk).delete()
        if deleted_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Job was not saved.', 'is_saved': False},
            status=status.HTTP_200_OK,
        )


class SavedJobsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsJobSeeker]
    serializer_class = JobListSerializer
    pagination_class = JobPagination

    def get_queryset(self):
        return (
            JobPosting.objects.filter(saved_by__user=self.request.user)
            .select_related(*JOB_SELECT_RELATED)
            .prefetch_related(*JOB_PREFETCH)
            .annotate(is_saved=Value(True, output_field=BooleanField()))
            .order_by('-saved_by__created_at')
        )


class MyJobsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsEmployer]
    serializer_class = JobOwnerSerializer
    pagination_class = JobPagination

    def get_queryset(self):
        try:
            employer = self.request.user.employer_profile
        except Exception:
            raise NotFound('Employer profile not found.')
        return (
            JobPosting.objects.filter(employer=employer)
            .select_related(*JOB_SELECT_RELATED)
            .prefetch_related(*JOB_PREFETCH)
        )


class JobCategoryCountsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        counts = (
            active_jobs_filter_qs()
            .values('category')
            .annotate(count=Count('id'))
        )
        count_map = {row['category']: row['count'] for row in counts}
        data = {
            choice.value: count_map.get(choice.value, 0)
            for choice in Profile.UserCategory
        }
        return Response(data)
