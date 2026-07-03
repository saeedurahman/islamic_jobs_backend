from rest_framework import generics
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny

from .models import Language, Skill
from .serializers import LanguageSerializer, SkillSerializer


class LanguageListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    pagination_class = None


class SkillListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    pagination_class = None
