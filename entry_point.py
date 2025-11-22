import azure.functions as func
from src.api.main import fastapi_app
from src.orchestrator.workflow import bp as orchestrator_bp
from src.agents import bp as agents_bp

# Intial the Main Function App with Fast API
app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)

# Register the Orchestrator Blueprint (The Manager of workflows)
app.register_functions(orchestrator_bp)

#register the Agents Blueprint (The AI Agents)
app.register_functions(agents_bp)






