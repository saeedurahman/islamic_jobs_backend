from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from employers.permissions import IsEmployer
from profiles.models import Profile

from .filters import JobPostingFilter
from .models import JobPosting
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


class JobListCreateView(generics.ListCreateAPIView):
    pagination_class = JobPagination
    filterset_class = JobPostingFilter
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['title', 'description']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsEmployer()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobOwnerSerializer
        return JobListSerializer

    def get_queryset(self):
        return active_jobs_queryset()

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
        return (
            JobPosting.objects.select_related(*JOB_SELECT_RELATED)
            .prefetch_related(*JOB_PREFETCH)
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
