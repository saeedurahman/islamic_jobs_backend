from rest_framework.permissions import BasePermission

from jobs.models import JobPosting


class IsApplicationApplicant(BasePermission):
    message = 'You can only withdraw your own applications.'

    def has_object_permission(self, request, view, obj):
        try:
            return obj.applicant_id == request.user.profile.id
        except Exception:
            return False


class IsJobPostingOwner(BasePermission):
    message = 'You do not have permission to view applications for this job.'

    def has_permission(self, request, view):
        job_id = view.kwargs.get('job_id')
        if not job_id:
            return False
        try:
            job = JobPosting.objects.get(pk=job_id)
            return job.employer_id == request.user.employer_profile.id
        except Exception:
            return False


class IsApplicationJobOwner(BasePermission):
    message = 'You do not have permission to manage this application.'

    def has_object_permission(self, request, view, obj):
        try:
            return obj.job.employer_id == request.user.employer_profile.id
        except Exception:
            return False
