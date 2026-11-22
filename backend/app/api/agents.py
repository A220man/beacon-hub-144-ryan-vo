"""Agent management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models import Agent, Model, Provider
from app.schemas import AgentCreate, AgentUpdate, AgentResponse, PaginatedResponse
router = APIRouter(prefix="/agents", tags=["agents"])
settings = get_settings()



@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent_data: AgentCreate, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)) -> AgentResponse:
    result = await db.execute(select(Model).join(Provider).where(Model.id == agent_data.model_id, Provider.owner_id == user_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found or not owned by user")
    agent = Agent(owner_id=user_id, model_id=agent_data.model_id, name=agent_data.name, description=agent_data.description, system_prompt=agent_data.system_prompt, temperature=agent_data.temperature, max_tokens=agent_data.max_tokens, tools=agent_data.tools, config=agent_data.config)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return AgentResponse.model_validate(agent)
