"""
Agent management API endpoints.

This module provides REST API endpoints for managing agents including
monitoring, configuration, and control operations.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.agents import (
    AgentCapability,
    RateLimitConfig,
    agent_config_manager,
    agent_monitor,
    agent_registry,
    isolation_manager,
    rate_limiter_manager,
)

router = APIRouter()


class AgentConfigUpdate(BaseModel):
    """Model for agent configuration updates."""

    enabled: Optional[bool] = None
    priority: Optional[int] = None
    circuit_breaker: Optional[Dict[str, Any]] = None
    rate_limiting: Optional[Dict[str, Any]] = None
    monitoring: Optional[Dict[str, Any]] = None
    timeouts: Optional[Dict[str, Any]] = None


class RateLimitConfigUpdate(BaseModel):
    """Model for rate limit configuration updates."""

    max_concurrent: Optional[int] = None
    min_time_ms: Optional[int] = None
    max_requests_per_minute: Optional[int] = None
    circuit_breaker_threshold: Optional[int] = None
    circuit_breaker_timeout: Optional[int] = None
    adaptive_adjustment: Optional[bool] = None
    burst_limit: Optional[int] = None
    burst_window_ms: Optional[int] = None


class AgentStatusResponse(BaseModel):
    """Model for agent status response."""

    name: str
    status: str
    is_healthy: bool
    capabilities: List[str]
    metrics: Dict[str, Any]


@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_agents():
    """Get information about all agents."""
    try:
        return agent_registry.get_agent_info()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agents: {str(e)}",
        )


@router.get("/{agent_name}", response_model=Dict[str, Any])
async def get_agent_details(agent_name: str):
    """Get detailed information about a specific agent."""
    try:
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found",
            )

        # Get agent info from registry
        agent_info = None
        for info in agent_registry.get_agent_info():
            if info["name"].lower() == agent_name.lower():
                agent_info = info
                break

        if not agent_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent info for '{agent_name}' not found",
            )

        # Add configuration information
        config = agent_config_manager.get_agent_config(agent_name)
        agent_info["configuration"] = config

        # Add isolation status
        isolation_status = isolation_manager.get_isolation_status()
        agent_info["isolation"] = {
            "quarantined": agent_name in isolation_status.get("quarantined_agents", {}),
            "failure_patterns": isolation_status.get("failure_patterns", {}).get(
                agent_name, {}
            ),
            "bulkhead_usage": isolation_status.get("bulkhead_usage", {}).get(
                agent_name, {}
            ),
        }

        return agent_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent details: {str(e)}",
        )


@router.get("/{agent_name}/health")
async def check_agent_health(agent_name: str):
    """Perform a health check on a specific agent."""
    try:
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found",
            )

        is_healthy, response_time, error_message = await agent.health_check()

        return {
            "agent_name": agent_name,
            "is_healthy": is_healthy,
            "response_time_ms": response_time,
            "error_message": error_message,
            "status": agent.status.value,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing health check: {str(e)}",
        )


@router.post("/{agent_name}/enable")
async def enable_agent(agent_name: str):
    """Enable an agent."""
    try:
        success = agent_registry.enable_agent(agent_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found",
            )

        return {"message": f"Agent '{agent_name}' enabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enabling agent: {str(e)}",
        )


@router.post("/{agent_name}/disable")
async def disable_agent(agent_name: str):
    """Disable an agent."""
    try:
        success = agent_registry.disable_agent(agent_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found",
            )

        return {"message": f"Agent '{agent_name}' disabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disabling agent: {str(e)}",
        )


@router.post("/{agent_name}/reset-circuit-breaker")
async def reset_agent_circuit_breaker(agent_name: str):
    """Reset the circuit breaker for an agent."""
    try:
        success = agent_registry.reset_agent_circuit_breaker(agent_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found",
            )

        return {"message": f"Circuit breaker reset for agent '{agent_name}'"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting circuit breaker: {str(e)}",
        )


@router.get("/{agent_name}/config")
async def get_agent_config(agent_name: str):
    """Get configuration for a specific agent."""
    try:
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found",
            )

        config = agent_config_manager.get_agent_config(agent_name)
        return {"agent_name": agent_name, "configuration": config}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent configuration: {str(e)}",
        )


@router.put("/{agent_name}/config")
async def update_agent_config(agent_name: str, config_update: AgentConfigUpdate):
    """Update configuration for a specific agent."""
    try:
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found",
            )

        # Convert Pydantic model to dict, excluding None values
        config_dict = config_update.dict(exclude_none=True)

        success = agent_config_manager.update_agent_config(agent_name, config_dict)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update agent configuration",
            )

        return {"message": f"Configuration updated for agent '{agent_name}'"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating agent configuration: {str(e)}",
        )


@router.post("/{agent_name}/config/reset")
async def reset_agent_config(agent_name: str):
    """Reset agent configuration to defaults."""
    try:
        success = agent_config_manager.reset_agent_config(agent_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found",
            )

        return {"message": f"Configuration reset for agent '{agent_name}'"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting agent configuration: {str(e)}",
        )


@router.get("/capabilities/{capability}")
async def get_agents_by_capability(capability: str):
    """Get agents that support a specific capability."""
    try:
        # Validate capability
        try:
            agent_capability = AgentCapability(capability)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid capability: {capability}. Valid capabilities: {[c.value for c in AgentCapability]}",
            )

        agents = agent_registry.get_agents_by_capability(agent_capability)

        return {
            "capability": capability,
            "agents": [
                {
                    "name": agent.name,
                    "status": agent.status.value,
                    "is_healthy": agent.is_healthy(),
                    "success_rate": agent.metrics.success_rate,
                }
                for agent in agents
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agents by capability: {str(e)}",
        )


@router.get("/monitoring/summary")
async def get_monitoring_summary():
    """Get monitoring summary for all agents."""
    try:
        return agent_monitor.get_agent_metrics_summary()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving monitoring summary: {str(e)}",
        )


@router.get("/monitoring/report")
async def get_performance_report():
    """Get comprehensive performance report."""
    try:
        return agent_monitor.get_performance_report()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating performance report: {str(e)}",
        )


@router.get("/isolation/status")
async def get_isolation_status():
    """Get error isolation status for all agents."""
    try:
        return isolation_manager.get_isolation_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving isolation status: {str(e)}",
        )


# Rate Limiting Endpoints


@router.get("/rate-limits/summary")
async def get_rate_limits_summary():
    """Get summary of all rate limiters."""
    try:
        return rate_limiter_manager.get_summary()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving rate limits summary: {str(e)}",
        )


@router.get("/rate-limits/metrics")
async def get_all_rate_limit_metrics():
    """Get rate limiting metrics for all agents."""
    try:
        return rate_limiter_manager.get_all_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving rate limit metrics: {str(e)}",
        )


@router.get("/{agent_name}/rate-limits")
async def get_agent_rate_limits(agent_name: str):
    """Get rate limiting configuration and metrics for a specific agent."""
    try:
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found",
            )

        metrics = rate_limiter_manager.get_agent_metrics(agent_name)
        return {"agent_name": agent_name, "rate_limits": metrics}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving rate limits for agent: {str(e)}",
        )


@router.put("/{agent_name}/rate-limits/config")
async def update_agent_rate_limit_config(
    agent_name: str, config_update: RateLimitConfigUpdate
):
    """Update rate limiting configuration for a specific agent."""
    try:
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found",
            )

        # Get current config
        current_metrics = rate_limiter_manager.get_agent_metrics(agent_name)
        if not current_metrics:
            # Create default config if none exists
            current_config = RateLimitConfig()
        else:
            current_config_dict = current_metrics["config"]
            current_config = RateLimitConfig(
                max_concurrent=current_config_dict["max_concurrent"],
                min_time_ms=current_config_dict["min_time_ms"],
                max_requests_per_minute=current_config_dict["max_requests_per_minute"],
                adaptive_adjustment=current_config_dict["adaptive_adjustment"],
            )

        # Update config with provided values
        update_dict = config_update.dict(exclude_none=True)
        for key, value in update_dict.items():
            if hasattr(current_config, key):
                setattr(current_config, key, value)

        # Apply the updated configuration
        success = rate_limiter_manager.update_agent_config(agent_name, current_config)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update rate limit configuration",
            )

        return {"message": f"Rate limit configuration updated for agent '{agent_name}'"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating rate limit configuration: {str(e)}",
        )


@router.post("/{agent_name}/rate-limits/reset-circuit")
async def reset_agent_rate_limit_circuit(agent_name: str):
    """Reset the rate limiting circuit breaker for an agent."""
    try:
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found",
            )

        success = rate_limiter_manager.reset_circuit_breaker(agent_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rate limiter not found for agent '{agent_name}'",
            )

        return {
            "message": f"Rate limiting circuit breaker reset for agent '{agent_name}'"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting rate limiting circuit breaker: {str(e)}",
        )
