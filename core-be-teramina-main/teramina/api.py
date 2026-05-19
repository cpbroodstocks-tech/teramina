from ninja import NinjaAPI

from teramina.user.controllers.registration_controller import (
    router as registration_router,
)
from teramina.user.controllers.profile_controller import router as profile_router
from teramina.authentication.controllers.authentication_controller import (
    router as authentication_router,
)

from teramina.farm.controllers.farm_controller import router as farm_router
from teramina.pond.controllers.pond_controller import router as pond_router
from teramina.cycle.controllers.cycle_controller import router as cycle_router

from teramina.cycle_data.controllers.cycle_data_controller import (
    router as cycle_data_router,
)
from teramina.dashboard.controllers.dashboard_controller import router as dashboard

from teramina.harvest.controllers.harvest_controller import router as harvest_router
from teramina.feeding.controllers.feed_controller import router as feed_router
from teramina.water_quality_dashboard.controllers.variable_controller import (
    router as variable_router,
)
from teramina.water_quality_dashboard.controllers.water_quality_controller import (
    router as wq_router,
)
from teramina.cost_data.controllers.cost_data_controller import router as cost_router

from teramina.google_sheets.controllers.sheet_controller import router as sheets_router
from teramina.harvest.controllers.harvest_scenario_controller import router as harvest_scenario_router
from teramina.dashboard.controllers.adaptive_forecast_controller import router as adaptive_forecast_router
from teramina.summarize.controllers.insight_controller import router as insight_router
from teramina.feeding.controllers.feeding_recommendation_controller import router as feed_rec_router
from teramina.benchmark.controllers.benchmark_controller import router as benchmark_router
from teramina.agent.controllers.agent_controller import router as agent_router
from teramina.agent.controllers.notes_controller import router as notes_router
from teramina.pl_report.controllers.pl_report_controller import router as pl_report_router
from teramina.pl_report.controllers.farm_pl_controller import router as farm_pl_router
from teramina.pl_report.controllers.share_controller import router as share_router
from teramina.pl_report.controllers.year_pl_controller import router as year_pl_router
from teramina.pl_report.controllers.pl_report_alias_controller import router as pl_alias_router

api = NinjaAPI(
    title="Teramina Backend API",
    version="v1.0.0",
    description="A documentation for Teramina",
)

api.add_router("/user", registration_router)
api.add_router("/user", authentication_router)
api.add_router("/user", profile_router)

api.add_router("/farm", farm_router)
api.add_router("/pond", pond_router)
api.add_router("/cycle", cycle_router)
api.add_router("/cycle-data", cycle_data_router)
api.add_router("/dashboard", dashboard)
api.add_router("/harvest", harvest_router)
api.add_router("/feeding", feed_router)
api.add_router("/water_quality_variable", variable_router)
api.add_router("/water_quality", wq_router)
api.add_router("/cost", cost_router)

api.add_router("/sheets", sheets_router)
api.add_router("/harvest", harvest_scenario_router)
api.add_router("/dashboard", adaptive_forecast_router)
api.add_router("/summarize", insight_router)
api.add_router("/feeding", feed_rec_router)
api.add_router("/benchmark", benchmark_router)
api.add_router("/agent", agent_router)
api.add_router("/agent", notes_router)
api.add_router("/cycle", pl_report_router)
api.add_router("/cycles", pl_alias_router)
api.add_router("/farm", farm_pl_router)
api.add_router("/farm", year_pl_router)
api.add_router("/report", share_router)
