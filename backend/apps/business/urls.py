from django.urls import path
from .views import DocumentListView, ReportListView, ApplicationListView

urlpatterns = [
    path("documents/", DocumentListView.as_view(), name="business-documents"),
    path("reports/", ReportListView.as_view(), name="business-reports"),
    path("applications/", ApplicationListView.as_view(), name="business-applications"),
]
