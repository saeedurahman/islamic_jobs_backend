from django.urls import path

from .views_reference import LanguageListView, SkillListView

urlpatterns = [
    path('languages/', LanguageListView.as_view(), name='profile-data-languages'),
    path('skills/', SkillListView.as_view(), name='profile-data-skills'),
]
