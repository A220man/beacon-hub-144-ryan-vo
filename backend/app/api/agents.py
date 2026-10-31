"""Agent management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.database import get_db
from app.models import Agent, Model, Provider
from app.schemas import AgentCreate, AgentUpdate, AgentResponse, PaginatedResponse
router = APIRouter(prefix="/agents", tags=["agents"])
settings = get_settings()
async def get_current_user_id() -> int:
    return 1
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
@router.get("", response_model=PaginatedResponse)
async def list_agents(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), is_active: bool | None = Query(None), db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)) -> PaginatedResponse:
    query = select(Agent).where(Agent.owner_id == user_id)
    if is_active is not None:
        query = query.where(Agent.is_active == is_active)
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    query = query.order_by(Agent.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    agents = result.scalars().all()
    return PaginatedResponse(items=[AgentResponse.model_validate(a) for a in agents], total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)
@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)) -> AgentResponse:
    result = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.owner_id == user_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse.model_validate(agent)
@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: int, agent_data: AgentUpdate, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)) -> AgentResponse:
    result = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.owner_id == user_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent_data.model_id is not None:
        model_result = await db.execute(select(Model).join(Provider).where(Model.id == agent_data.model_id, Provider.owner_id == user_id))
        model = model_result.scalar_one_or_none()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found or not owned by user")
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    await db.commit()
    await db.refresh(agent)
    return AgentResponse.model_validate(agent)
@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)) -> None:
    result = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.owner_id == user_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await db.delete(agent)
    await db.commit()
