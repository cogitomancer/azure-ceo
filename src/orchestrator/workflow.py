import azure.functions as func
import azure.functions.durable as df
import logging
import json

# Orchestrator Blueprint
bp = func.Blueprint()


#1. QUEUE TRIGGER (The "Starter")
# Listens to 'ai-job-queue'. When a message arrives, it starts a new orchestration instance.

@bp.function_name("OrchestratorStarter")
@bp.queue_trigger(arg_name="msg", queue_name="ai-job-queue", connection="AzureWebJobsStorage")
@bp.durable_client_input(client_name="client")
async def queue_start(msg: func.QueueMessage, client: df.DurableOrchestrationClient):
    try:
        payload = json.loads(msg.get_body().decode('utf-8'))
        instance_id = await client.start_new("PersonalizationOrchestrator", client_input=payload)
        logging.info(f"Started orchestration with ID = '{instance_id}' for message: {payload}")
    except Exception as e:
        logging.error(f"Failed to start orchestration: {e}")


# 2. THE ORCHESTRATOR ("The Workflow")
@bp.orchestration_trigger(context_name="context")
def PersonalizationOrchestrator(context: df.DurableOrchestrationContext):
    # 1. Get Input (Customer Event)
    event_data = context.get_input()

    #2. Call Agemmt 1: Sentiment Analysis
    enriched_data  = yield context.call_activity("Agent_Sentiment_Analysis", event_data)

    #3. Call Agent 2, Segmentation Analysis
    segment_data = yield context.call_activity("Agent_Segmentation", enriched_data)

    #4. Call Agent 3 Retrieval Agent
    # we might ne to parallelize or segment the data first
    retrieved_content = yield context.call_activity("Agent_Retrieval", segment_data)

    #5. Call Agnt 4 Variant Generation Agent
    #Prepare input for generation
    gen_input = {
        "segment": segment_data['segment']
        ,"content": retrieved_content
        ,"user_id": event_data['user_id']
    }

    variants = yield context.call_activity("Agent_VariantGeneration", gen_input)

     # 6. Call Agent 5: Safety Check
    safety_result = yield context.call_activity("Agent_SafetyCheck", variants)
    
    if not safety_result['approved']:
        return {"status": "blocked", "reason": "No safe variants generated"}

    # 7. Call Agent 6: Uplift/Experiment
    assignment = yield context.call_activity("Agent_UpliftExperiment", safety_result)
    
    # 8. Call Agent 7: Reporting/Finalization
    final_report = yield context.call_activity("Agent_Reporting", assignment)
    
    return final_report