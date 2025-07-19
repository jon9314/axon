# axon/backend/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from memory.memory_handler import MemoryHandler
from config.settings import settings
from agent.llm_router import LLMRouter
import re
import logging

# --- NEW: Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# Create a FastAPI application instance
app = FastAPI(
    title="Axon Backend",
    description="The backend service for the Axon project, handling API requests and WebSocket connections.",
    version="0.1.0",
)

# Instantiate the handlers
memory_handler = MemoryHandler(db_uri=settings.database.postgres_uri)
llm_router = LLMRouter()

@app.on_event("shutdown")
def shutdown_event():
    memory_handler.close_connection()
    logging.info("Application shutdown: Database connection closed.")

@app.get("/")
async def read_root():
    return {"message": "Axon backend is running and connected to memory."}

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    thread_id = "user_session_123"
    logging.info(f"Client connected to WebSocket for thread_id: {thread_id}")

    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Received message: '{data}'")

            response_message = ""
            remember_match = re.match(r"remember (.*) is (.*)", data, re.IGNORECASE)

            if remember_match:
                key = remember_match.group(1).strip()
                value = remember_match.group(2).strip()
                memory_handler.add_fact(thread_id, key, value)
                response_message = f"OK, I'll remember that {key} is {value}."

            elif "what is" in data.lower():
                key_match = re.search(r"what is (.*)\?", data, re.IGNORECASE)
                key = key_match.group(1).strip() if key_match else data.lower().replace("what is", "").strip()
                fact = memory_handler.get_fact(thread_id, key)
                if fact:
                    response_message = f"You told me that {key} is {fact}."
                else:
                    response_message = f"I don't have a memory for '{key}'."
            else:
                logging.info(f"No command recognized. Routing to LLM.")
                response_message = llm_router.get_response(data, model=settings.llm.default_local_model)

            logging.info(f"Sending response: '{response_message}'")
            await websocket.send_text(response_message)

    except WebSocketDisconnect:
        logging.info("Client disconnected.")
    except Exception as e:
        # --- NEW: Detailed Error Logging ---
        # This will print the full error traceback to your terminal
        logging.error("An error occurred in the WebSocket:", exc_info=True)