"""
Docker cleanup and monitoring API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from models.user import User
from core.dependencies import get_current_user, require_admin
from services.docker_cleanup_service import docker_cleanup_service


router = APIRouter(prefix="/docker", tags=["docker"])


@router.get("/disk-usage", response_model=Dict[str, Any])
async def get_docker_disk_usage(
    current_user: User = Depends(require_admin),
):
    """
    Get Docker disk usage statistics.

    Shows space used by images, containers, volumes, and build cache.

    Requires admin role.
    """
    try:
        usage = await docker_cleanup_service.get_disk_usage()
        return usage

    except RuntimeError as e:
        import traceback
        print(f"⚠️  RuntimeError getting Docker disk usage: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        print(f"⚠️  Failed to get Docker disk usage: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Docker disk usage: {str(e)}"
        )


@router.post("/prune-images", response_model=Dict[str, Any])
async def prune_docker_images(
    current_user: User = Depends(require_admin),
):
    """
    Remove unused Minecraft server images.

    This will ONLY delete itzg/minecraft-server images not referenced by any container.
    Other Docker images on your system will not be affected.

    Requires admin role.
    """
    try:
        result = await docker_cleanup_service.prune_images(all=True)
        return result

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        print(f"⚠️  Failed to prune Docker images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prune Docker images"
        )


@router.post("/prune-containers", response_model=Dict[str, Any])
async def prune_docker_containers(
    current_user: User = Depends(require_admin),
):
    """
    Remove stopped Mineploy-managed containers.

    This will ONLY delete stopped containers managed by Mineploy (with mineploy.managed=true label).
    Other Docker containers on your system will not be affected.
    Active Mineploy servers will not be affected.

    Requires admin role.
    """
    try:
        result = await docker_cleanup_service.prune_containers()
        return result

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        print(f"⚠️  Failed to prune Docker containers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prune Docker containers"
        )


@router.post("/prune-volumes", response_model=Dict[str, Any])
async def prune_docker_volumes(
    current_user: User = Depends(require_admin),
):
    """
    Remove unused volumes.

    WARNING: This will permanently delete orphaned Minecraft world data
    that is not attached to any container.

    Requires admin role.
    """
    try:
        result = await docker_cleanup_service.prune_volumes()
        return result

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        print(f"⚠️  Failed to prune Docker volumes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prune Docker volumes"
        )


@router.post("/prune-networks", response_model=Dict[str, Any])
async def prune_docker_networks(
    current_user: User = Depends(require_admin),
):
    """
    Remove unused networks.

    This will delete networks not used by any container.
    The minecraft_network will not be removed if it's in use.

    Requires admin role.
    """
    try:
        result = await docker_cleanup_service.prune_networks()
        return result

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        print(f"⚠️  Failed to prune Docker networks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prune Docker networks"
        )


@router.post("/prune-all", response_model=Dict[str, Any])
async def prune_all_docker_resources(
    current_user: User = Depends(require_admin),
):
    """
    Perform complete cleanup of all unused Docker resources.

    This will remove:
    - Unused images
    - Stopped containers
    - Unused volumes (WARNING: includes orphaned world data)
    - Unused networks
    - Build cache

    This is equivalent to running 'docker system prune -af --volumes'.

    Requires admin role.
    """
    try:
        result = await docker_cleanup_service.prune_all()
        return result

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        print(f"⚠️  Failed to prune all Docker resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prune all Docker resources"
        )
