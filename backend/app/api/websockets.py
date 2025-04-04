from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Dict, List
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User, UserRole
from app.models.job import Job
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["websockets"])

# OAuth2 scheme for WebSocket (we'll use the token from the query parameter)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# WebSocket manager to handle connections
class WebSocketManager:
    def __init__(self):
        # Dictionary to store connections: {user_id: List[WebSocket]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user: User):
        await websocket.accept()
        if user.id not in self.active_connections:
            self.active_connections[user.id] = []
        self.active_connections[user.id].append(websocket)
        logger.info(f"User {user.email} (ID: {user.id}) connected via WebSocket")

    def disconnect(self, websocket: WebSocket, user: User):
        if user.id in self.active_connections:
            self.active_connections[user.id].remove(websocket)
            if not self.active_connections[user.id]:
                del self.active_connections[user.id]
        logger.info(f"User {user.email} (ID: {user.id}) disconnected from WebSocket")

    async def broadcast_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {str(e)}")

    async def broadcast_job_update(self, job: Job, db: Session):
        """
        Broadcast a job update to the relevant users (customer, technician, admins).
        """
        message = {
            "type": "job_update",
            "job_id": job.id,
            "status": job.status.value,
            "description": job.description,
            "technician_id": job.technician_id,
            "user_id": job.user_id,
            "updated_at": job.date_modified.isoformat() if job.date_modified else None
        }

        # Notify the customer who created the job
        if job.user_id:
            await self.broadcast_to_user(job.user_id, message)

        # Notify the assigned technician
        if job.technician_id:
            await self.broadcast_to_user(job.technician_id, message)

        # Notify all admins
        admins = db.query(User).filter(User.role == UserRole.ADMIN).all()
        for admin in admins:
            await self.broadcast_to_user(admin.id, message)

# Instantiate the WebSocket manager
websocket_manager = WebSocketManager()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time updates.
    Clients connect with a JWT token and receive updates for relevant jobs.
    """
    # Authenticate the user
    try:
        user = await get_current_user(token=token, db=db)
        if not user.is_active:
            await websocket.close(code=1008, reason="Inactive user")
            return
    except HTTPException as e:
        await websocket.close(code=1008, reason="Invalid token")
        logger.error(f"WebSocket authentication failed: {str(e)}")
        return

    # Connect the user
    await websocket_manager.connect(websocket, user)

    try:
        # Keep the connection alive and listen for client messages
        while True:
            # Receive messages from the client (optional, for ping/pong or other interactions)
            data = await websocket.receive_text()
            logger.info(f"Received message from user {user.email}: {data}")
            # Respond with a pong (optional)
            await websocket.send_json({"type": "pong", "message": "Ping received"})
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user)
    except Exception as e:
        logger.error(f"WebSocket error for user {user.email}: {str(e)}")
        websocket_manager.disconnect(websocket, user)
        await websocket.close(code=1011, reason="Internal server error")

# Function to broadcast job updates (called from other parts of the app)
async def broadcast_job_update(job_id: str, db: Session):
    """
    Broadcast a job update to connected clients.
    Called when a job is updated (e.g., status change).
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        await websocket_manager.broadcast_job_update(job, db)
    else:
        logger.warning(f"Job {job_id} not found for broadcasting update")