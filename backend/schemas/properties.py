"""
Schemas for Minecraft server.properties configuration.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ServerPropertiesResponse(BaseModel):
    """Response schema for server properties."""

    # Server settings
    motd: str = Field(..., description="Message of the day")
    max_players: int = Field(..., ge=1, le=100000, description="Maximum number of players")
    server_port: int = Field(..., ge=1, le=65535, description="Server port")

    # Gameplay settings
    gamemode: str = Field(..., description="Default game mode (survival, creative, adventure, spectator)")
    difficulty: str = Field(..., description="Difficulty level (peaceful, easy, normal, hard)")
    hardcore: bool = Field(..., description="Hardcore mode")
    pvp: bool = Field(..., description="Player vs Player enabled")

    # World settings
    level_name: str = Field(..., description="World name")
    level_seed: str = Field(..., description="World seed (empty for random)")
    level_type: str = Field(..., description="World type (default, flat, largeBiomes, amplified, buffet)")
    generate_structures: bool = Field(..., description="Generate structures (villages, etc)")
    spawn_monsters: bool = Field(..., description="Spawn monsters")
    spawn_animals: bool = Field(..., description="Spawn animals")
    spawn_npcs: bool = Field(..., description="Spawn villagers")

    # Performance settings
    view_distance: int = Field(..., ge=3, le=32, description="View distance in chunks")
    simulation_distance: int = Field(..., ge=3, le=32, description="Simulation distance in chunks")
    max_tick_time: int = Field(..., description="Maximum tick time in milliseconds (-1 to disable)")

    # Network settings
    online_mode: bool = Field(..., description="Online mode (authenticate with Mojang)")
    enable_status: bool = Field(..., description="Enable server list status")
    allow_flight: bool = Field(..., description="Allow flight")
    max_world_size: int = Field(..., description="Maximum world size")

    # Spawn settings
    spawn_protection: int = Field(..., ge=0, description="Spawn protection radius")
    force_gamemode: bool = Field(..., description="Force players to join in default gamemode")

    # Other settings
    white_list: bool = Field(..., description="Enable whitelist")
    enforce_whitelist: bool = Field(..., description="Enforce whitelist (kick players not on whitelist)")
    resource_pack: str = Field(..., description="URL to resource pack")
    resource_pack_prompt: str = Field(..., description="Resource pack prompt message")
    require_resource_pack: bool = Field(..., description="Require resource pack")
    enable_command_block: bool = Field(..., description="Enable command blocks")
    function_permission_level: int = Field(..., ge=1, le=4, description="Permission level for functions")
    op_permission_level: int = Field(..., ge=1, le=4, description="Permission level for operators")

    # RCON settings
    enable_rcon: bool = Field(..., description="Enable RCON")
    rcon_port: int = Field(..., ge=1, le=65535, description="RCON port")
    rcon_password: str = Field(..., description="RCON password")

    # Query settings
    enable_query: bool = Field(..., description="Enable GameSpy4 protocol server listener")
    query_port: int = Field(..., ge=1, le=65535, description="Query port")

    @field_validator('gamemode')
    @classmethod
    def validate_gamemode(cls, v: str) -> str:
        allowed = ['survival', 'creative', 'adventure', 'spectator']
        if v.lower() not in allowed:
            raise ValueError(f'gamemode must be one of: {", ".join(allowed)}')
        return v.lower()

    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        allowed = ['peaceful', 'easy', 'normal', 'hard']
        if v.lower() not in allowed:
            raise ValueError(f'difficulty must be one of: {", ".join(allowed)}')
        return v.lower()

    @field_validator('level_type')
    @classmethod
    def validate_level_type(cls, v: str) -> str:
        allowed = ['default', 'flat', 'largeBiomes', 'amplified', 'buffet', 'minecraft:normal', 'minecraft:flat', 'minecraft:large_biomes', 'minecraft:amplified']
        if v not in allowed:
            raise ValueError(f'level_type must be one of: {", ".join(allowed)}')
        return v


class ServerPropertiesUpdate(BaseModel):
    """Schema for updating server properties (all fields optional)."""

    # Server settings
    motd: Optional[str] = Field(None, description="Message of the day")
    max_players: Optional[int] = Field(None, ge=1, le=100000, description="Maximum number of players")

    # Gameplay settings
    gamemode: Optional[str] = Field(None, description="Default game mode")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    hardcore: Optional[bool] = Field(None, description="Hardcore mode")
    pvp: Optional[bool] = Field(None, description="Player vs Player enabled")

    # World settings
    level_seed: Optional[str] = Field(None, description="World seed (empty for random)")
    level_type: Optional[str] = Field(None, description="World type")
    generate_structures: Optional[bool] = Field(None, description="Generate structures")
    spawn_monsters: Optional[bool] = Field(None, description="Spawn monsters")
    spawn_animals: Optional[bool] = Field(None, description="Spawn animals")
    spawn_npcs: Optional[bool] = Field(None, description="Spawn villagers")

    # Performance settings
    view_distance: Optional[int] = Field(None, ge=3, le=32, description="View distance in chunks")
    simulation_distance: Optional[int] = Field(None, ge=3, le=32, description="Simulation distance in chunks")
    max_tick_time: Optional[int] = Field(None, description="Maximum tick time in milliseconds")

    # Network settings
    online_mode: Optional[bool] = Field(None, description="Online mode")
    enable_status: Optional[bool] = Field(None, description="Enable server list status")
    allow_flight: Optional[bool] = Field(None, description="Allow flight")
    max_world_size: Optional[int] = Field(None, description="Maximum world size")

    # Spawn settings
    spawn_protection: Optional[int] = Field(None, ge=0, description="Spawn protection radius")
    force_gamemode: Optional[bool] = Field(None, description="Force players to join in default gamemode")

    # Other settings
    white_list: Optional[bool] = Field(None, description="Enable whitelist")
    enforce_whitelist: Optional[bool] = Field(None, description="Enforce whitelist")
    resource_pack: Optional[str] = Field(None, description="URL to resource pack")
    resource_pack_prompt: Optional[str] = Field(None, description="Resource pack prompt message")
    require_resource_pack: Optional[bool] = Field(None, description="Require resource pack")
    enable_command_block: Optional[bool] = Field(None, description="Enable command blocks")
    function_permission_level: Optional[int] = Field(None, ge=1, le=4, description="Permission level for functions")
    op_permission_level: Optional[int] = Field(None, ge=1, le=4, description="Permission level for operators")

    # Query settings
    enable_query: Optional[bool] = Field(None, description="Enable GameSpy4 protocol server listener")

    @field_validator('gamemode')
    @classmethod
    def validate_gamemode(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = ['survival', 'creative', 'adventure', 'spectator']
        if v.lower() not in allowed:
            raise ValueError(f'gamemode must be one of: {", ".join(allowed)}')
        return v.lower()

    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = ['peaceful', 'easy', 'normal', 'hard']
        if v.lower() not in allowed:
            raise ValueError(f'difficulty must be one of: {", ".join(allowed)}')
        return v.lower()

    @field_validator('level_type')
    @classmethod
    def validate_level_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = ['default', 'flat', 'largeBiomes', 'amplified', 'buffet', 'minecraft:normal', 'minecraft:flat', 'minecraft:large_biomes', 'minecraft:amplified']
        if v not in allowed:
            raise ValueError(f'level_type must be one of: {", ".join(allowed)}')
        return v
