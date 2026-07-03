from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from employers.permissions import IsEmployer
from jobs.models import JobPosting
from profiles.permissions import IsJobSeeker

from .filters import ApplicationFilter
from .models import Application
from .notifications import notify_applicant_status_change, notify_employer_new_application
from .permissions import (
    IsApplicationApplicant,
    IsApplicationJobOwner,
    IsJobPostingOwner,
)
from .serializers import (
    APPLICANT_PROFILE_PREFETCH,
    APPLICANT_PROFILE_SELECT_RELATED,
    ApplicationCreateSerializer,
    ApplicationEmployerSerializer,
    ApplicationSeekerSerializer,
    ApplicationStatusUpdateSerializer,
)


def _applications_with_applicant_profile():
    return (
        Application.objects.select_related(*APPLICANT_PROFILE_SELECT_RELATED)
        .prefetch_related(*APPLICANT_PROFILE_PREFETCH)
    )


class ApplicationCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsJobSeeker]
    serializer_class = ApplicationCreateSerializer

    def perform_create(self, serializer):
        application = serializer.save()
        notify_employer_new_application(application)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = (
            Application.objects.select_related('job', 'job__employer', 'job__city')
            .get(pk=serializer.instance.pk)
        )
        headers = self.get_success_headers(serializer.data)
        output = ApplicationSeekerSerializer(instance, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)


class MyApplicationsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsJobSeeker]
    serializer_class = ApplicationSeekerSerializer
    filterset_class = ApplicationFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        try:
            profile = self.request.user.profile
        except Exception:
            raise NotFound('Job seeker profile not found.')
        return (
            Application.objects.filter(applicant=profile)
            .select_related('job', 'job__employer', 'job__city')
            .order_by('-applied_at')
        )


class JobApplicationsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsEmployer, IsJobPostingOwner]
    serializer_class = ApplicationEmployerSerializer
    filterset_class = ApplicationFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        job_id = self.kwargs['job_id']
        return (
            _applications_with_applicant_profile()
            .filter(job_id=job_id)
            .order_by('-applied_at')
        )


class ApplicationStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsEmployer, IsApplicationJobOwner]
    serializer_class = ApplicationStatusUpdateSerializer
    lookup_url_kwarg = 'pk'
    http_method_names = ['patch', 'head', 'options']

    def get_queryset(self):
        return _applications_with_applicant_profile().select_related(
            'job', 'job__employer'
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_status = instance.status
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if instance.status != old_status:
            notify_applicant_status_change(instance)
        output = ApplicationEmployerSerializer(instance, context=self.get_serializer_context())
        return Response(output.data)


class ApplicationWithdrawView(APIView):
    permission_classes = [IsAuthenticated, IsJobSeeker, IsApplicationApplicant]

    def patch(self, request, pk):
        try:
            application = Application.objects.select_related(
                'job', 'job__employer', 'job__city'
            ).get(pk=pk, applicant=request.user.profile)
        except Application.DoesNotExist:
            raise NotFound('Application not found.')
        self.check_object_permissions(request, application)

        if application.status == Application.Status.WITHDRAWN:
            return Response(
                {'detail': 'Application is already withdrawn.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if application.status == Application.Status.HIRED:
            return Response(
                {'detail': 'Cannot withdraw a hired application.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application.status = Application.Status.WITHDRAWN
        application.save(update_fields=['status', 'status_updated_at'])
        serializer = ApplicationSeekerSerializer(application, context={'request': request})
        return Response(serializer.data)
