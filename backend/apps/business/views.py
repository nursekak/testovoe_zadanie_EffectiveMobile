from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from apps.access_control.decorators import require_permission

MOCK_DOCUMENTS = [
    {"id": 1, "title": "Договор №2024-001", "type": "contract", "status": "active"},
    {"id": 2, "title": "Акт выполненных работ", "type": "act", "status": "draft"},
    {"id": 3, "title": "Спецификация к проекту Alpha", "type": "spec", "status": "active"},
]

MOCK_REPORTS = [
    {"id": 1, "title": "Финансовый отчёт Q1 2024", "period": "2024-Q1", "status": "approved"},
    {"id": 2, "title": "Операционный отчёт Q2 2024", "period": "2024-Q2", "status": "pending"},
]

MOCK_APPLICATIONS = [
    {"id": 1, "title": "Заявка на командировку #101", "applicant": "Иванов И.И.", "status": "open"},
    {"id": 2, "title": "Заявка на отпуск #102", "applicant": "Петрова А.В.", "status": "approved"},
    {"id": 3, "title": "Заявка на оборудование #103", "applicant": "Сидоров К.О.", "status": "open"},
]


class DocumentListView(APIView):
    @extend_schema(tags=["business"], summary="Список документов [требует document:read]")
    @require_permission("document", "read")
    def get(self, request):
        return Response({"count": len(MOCK_DOCUMENTS), "results": MOCK_DOCUMENTS})

    @extend_schema(tags=["business"], summary="Создать документ [требует document:create]")
    @require_permission("document", "create")
    def post(self, request):
        new_doc = {
            "id": len(MOCK_DOCUMENTS) + 1,
            "title": request.data.get("title", "Новый документ"),
            "type": request.data.get("type", "other"),
            "status": "draft",
        }
        return Response(new_doc, status=status.HTTP_201_CREATED)


class ReportListView(APIView):
    @extend_schema(tags=["business"], summary="Список отчётов [требует report:read]")
    @require_permission("report", "read")
    def get(self, request):
        return Response({"count": len(MOCK_REPORTS), "results": MOCK_REPORTS})

    @extend_schema(tags=["business"], summary="Создать отчёт [требует report:create]")
    @require_permission("report", "create")
    def post(self, request):
        new_report = {
            "id": len(MOCK_REPORTS) + 1,
            "title": request.data.get("title", "Новый отчёт"),
            "period": request.data.get("period", ""),
            "status": "pending",
        }
        return Response(new_report, status=status.HTTP_201_CREATED)


class ApplicationListView(APIView):
    @extend_schema(tags=["business"], summary="Список заявок [требует application:read]")
    @require_permission("application", "read")
    def get(self, request):
        return Response({"count": len(MOCK_APPLICATIONS), "results": MOCK_APPLICATIONS})

    @extend_schema(tags=["business"], summary="Создать заявку [требует application:create]")
    @require_permission("application", "create")
    def post(self, request):
        new_app = {
            "id": len(MOCK_APPLICATIONS) + 1,
            "title": request.data.get("title", "Новая заявка"),
            "applicant": request.user.full_name,
            "status": "open",
        }
        return Response(new_app, status=status.HTTP_201_CREATED)
