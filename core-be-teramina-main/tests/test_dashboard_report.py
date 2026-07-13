import base64
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


class TestDashboardReportRoutes:
    @patch("teramina.dashboard.controllers.dashboard_controller.cache")
    @patch("teramina.dashboard.controllers.dashboard_controller._owns_dashboard_context", return_value=True)
    @patch("teramina.dashboard.controllers.dashboard_controller.generate_overview_report")
    @patch("teramina.dashboard.controllers.dashboard_controller.get_signed_in_user")
    def test_create_report_queues_task_and_returns_task_id(self, mock_user, mock_task, _mock_owner, mock_cache):
        from teramina.dashboard.controllers.dashboard_controller import create_report

        mock_user.return_value = SimpleNamespace(id="user_001")
        mock_task.delay.return_value = SimpleNamespace(id="task_123")

        response = create_report(
            MagicMock(),
            {
                "farm_id": "farm_001",
                "pond_id": "pond_001",
                "cycle_id": "cycle_001",
                "date": "",
            },
        )

        assert response == {"task_id": "task_123"}
        mock_task.delay.assert_called_once_with(
            "farm_001",
            "pond_001",
            "cycle_001",
            None,
            "user_001",
        )
        mock_cache.set.assert_called_once_with("dashboard_report_owner:task_123", "user_001", timeout=3600)

    @patch("teramina.dashboard.controllers.dashboard_controller.get_signed_in_user")
    @patch("teramina.dashboard.controllers.dashboard_controller.cache")
    @patch("teramina.dashboard.controllers.dashboard_controller.AsyncResult")
    def test_get_report_pending_returns_json_status(self, MockAsyncResult, mock_cache, mock_user):
        from teramina.dashboard.controllers.dashboard_controller import get_report

        MockAsyncResult.return_value = SimpleNamespace(state="PENDING")
        mock_user.return_value = SimpleNamespace(id="user_001")
        mock_cache.get.return_value = "user_001"

        response = get_report(MagicMock(), "task_123")

        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        assert b'"status": "PENDING"' in response.content

    @patch("teramina.dashboard.controllers.dashboard_controller.get_signed_in_user")
    @patch("teramina.dashboard.controllers.dashboard_controller.cache")
    @patch("teramina.dashboard.controllers.dashboard_controller.AsyncResult")
    def test_get_report_failure_returns_failure_json(self, MockAsyncResult, mock_cache, mock_user):
        from teramina.dashboard.controllers.dashboard_controller import get_report

        MockAsyncResult.return_value = SimpleNamespace(state="FAILURE", result=RuntimeError("boom"))
        mock_user.return_value = SimpleNamespace(id="user_001")
        mock_cache.get.return_value = "user_001"

        response = get_report(MagicMock(), "task_123")

        assert response.status_code == 500
        assert b'"status": "FAILURE"' in response.content
        assert b"boom" in response.content
        mock_cache.delete.assert_called_once_with("dashboard_report_owner:task_123")

    @patch("teramina.dashboard.controllers.dashboard_controller.get_signed_in_user")
    @patch("teramina.dashboard.controllers.dashboard_controller.cache")
    @patch("teramina.dashboard.controllers.dashboard_controller.AsyncResult")
    def test_get_report_success_returns_pdf(self, MockAsyncResult, mock_cache, mock_user):
        from teramina.dashboard.controllers.dashboard_controller import get_report

        pdf_bytes = b"%PDF-1.4 fake"
        MockAsyncResult.return_value = SimpleNamespace(
            state="SUCCESS",
            result={
                "status": "SUCCESS",
                "content_type": "application/pdf",
                "filename": "report_teramina.pdf",
                "data_base64": base64.b64encode(pdf_bytes).decode("ascii"),
            },
        )
        mock_user.return_value = SimpleNamespace(id="user_001")
        mock_cache.get.return_value = "user_001"

        response = get_report(MagicMock(), "task_123")

        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert response["Content-Disposition"] == 'attachment; filename="report_teramina.pdf"'
        assert response.content == pdf_bytes
        mock_cache.delete.assert_called_once_with("dashboard_report_owner:task_123")

    @patch("teramina.dashboard.controllers.dashboard_controller.get_signed_in_user")
    @patch("teramina.dashboard.controllers.dashboard_controller.cache")
    @patch("teramina.dashboard.controllers.dashboard_controller.AsyncResult")
    def test_get_report_hides_another_users_task(self, MockAsyncResult, mock_cache, mock_user):
        from teramina.dashboard.controllers.dashboard_controller import get_report

        mock_user.return_value = SimpleNamespace(id="user_002")
        mock_cache.get.return_value = "user_001"

        response = get_report(MagicMock(), "task_123")

        assert response.status_code == 404
        MockAsyncResult.assert_not_called()


class TestDashboardReportTask:
    @patch("teramina.dashboard.tasks.report_tasks.generate_pdf_report_with_data")
    @patch("teramina.dashboard.tasks.report_tasks.DashboardOverview")
    def test_generate_overview_report_returns_json_serializable_pdf(self, MockDashboard, mock_pdf):
        from teramina.dashboard.tasks.report_tasks import generate_overview_report

        async def fake_download_report_pdf():
            return {"content": []}

        MockDashboard.return_value.download_report_pdf = fake_download_report_pdf
        mock_pdf.return_value = b"%PDF-1.4 fake"

        result = generate_overview_report(
            "farm_001",
            "pond_001",
            "cycle_001",
            "01/31/2024",
            "user_001",
        )

        assert result["status"] == "SUCCESS"
        assert result["content_type"] == "application/pdf"
        assert base64.b64decode(result["data_base64"]) == b"%PDF-1.4 fake"
        MockDashboard.assert_called_once_with(
            farm_id="farm_001",
            pond_id="pond_001",
            cycle_id="cycle_001",
            date="01/31/2024",
            user_id="user_001",
        )
