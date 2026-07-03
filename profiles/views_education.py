from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated

from .models import (
    AsriEducation,
    DarseNizami,
    HifzEducation,
    Ijazah,
    MuftiCourse,
    NazraQirat,
    Profile,
)
from .permissions import IsJobSeeker
from .serializers import (
    AsriEducationSerializer,
    DarseNizamiSerializer,
    HifzEducationSerializer,
    IjazahSerializer,
    MuftiCourseSerializer,
    NazraQiratSerializer,
)


class OwnerEducationMixin:
    """Restrict education records to the authenticated job seeker's own profile."""

    permission_classes = [IsAuthenticated, IsJobSeeker]

    def get_profile(self):
        try:
            return self.request.user.profile
        except Profile.DoesNotExist:
            raise NotFound('Job seeker profile not found.')

    def get_queryset(self):
        return self.model.objects.filter(profile=self.get_profile())


class OwnerEducationCreateView(OwnerEducationMixin, generics.CreateAPIView):
    def perform_create(self, serializer):
        serializer.save(profile=self.get_profile())


class OwnerEducationDetailView(OwnerEducationMixin, generics.UpdateAPIView, generics.DestroyAPIView):
    http_method_names = ['patch', 'delete', 'head', 'options']
    lookup_url_kwarg = 'pk'


class HifzEducationCreateView(OwnerEducationCreateView):
    model = HifzEducation
    serializer_class = HifzEducationSerializer
    queryset = HifzEducation.objects.all()


class HifzEducationDetailView(OwnerEducationDetailView):
    model = HifzEducation
    serializer_class = HifzEducationSerializer
    queryset = HifzEducation.objects.all()


class DarseNizamiCreateView(OwnerEducationCreateView):
    model = DarseNizami
    serializer_class = DarseNizamiSerializer
    queryset = DarseNizami.objects.all()


class DarseNizamiDetailView(OwnerEducationDetailView):
    model = DarseNizami
    serializer_class = DarseNizamiSerializer
    queryset = DarseNizami.objects.all()


class MuftiCourseCreateView(OwnerEducationCreateView):
    model = MuftiCourse
    serializer_class = MuftiCourseSerializer
    queryset = MuftiCourse.objects.all()


class MuftiCourseDetailView(OwnerEducationDetailView):
    model = MuftiCourse
    serializer_class = MuftiCourseSerializer
    queryset = MuftiCourse.objects.all()


class IjazahCreateView(OwnerEducationCreateView):
    model = Ijazah
    serializer_class = IjazahSerializer
    queryset = Ijazah.objects.all()


class IjazahDetailView(OwnerEducationDetailView):
    model = Ijazah
    serializer_class = IjazahSerializer
    queryset = Ijazah.objects.all()


class NazraQiratCreateView(OwnerEducationCreateView):
    model = NazraQirat
    serializer_class = NazraQiratSerializer
    queryset = NazraQirat.objects.all()


class NazraQiratDetailView(OwnerEducationDetailView):
    model = NazraQirat
    serializer_class = NazraQiratSerializer
    queryset = NazraQirat.objects.all()


class AsriEducationCreateView(OwnerEducationCreateView):
    model = AsriEducation
    serializer_class = AsriEducationSerializer
    queryset = AsriEducation.objects.all()


class AsriEducationDetailView(OwnerEducationDetailView):
    model = AsriEducation
    serializer_class = AsriEducationSerializer
    queryset = AsriEducation.objects.all()
