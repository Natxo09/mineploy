import type { ServerProperties } from "@/types";
import {
  GAMEMODE_OPTIONS,
  DIFFICULTY_OPTIONS,
  LEVEL_TYPE_OPTIONS,
  PROPERTY_CATEGORIES,
} from "@/types";

export interface PropertyMetadata {
  key: keyof ServerProperties;
  label: string;
  description: string;
  category: string;
  type: "string" | "number" | "boolean" | "select";
  options?: readonly string[];
  min?: number;
  max?: number;
  step?: number;
  readOnly?: boolean;
  requiresRestart?: boolean;
  requiresWorldRegen?: boolean;
  placeholder?: string;
}

export const PROPERTY_METADATA: PropertyMetadata[] = [
  // SERVER SETTINGS
  {
    key: "motd",
    label: "Server Name",
    description: "Name of the server displayed in the server list",
    category: PROPERTY_CATEGORIES.SERVER,
    type: "string",
    requiresRestart: true,
    placeholder: "A Minecraft Server",
  },
  {
    key: "max_players",
    label: "Max Players",
    description: "Maximum number of players that can join",
    category: PROPERTY_CATEGORIES.SERVER,
    type: "number",
    min: 1,
    max: 100000,
    requiresRestart: true,
  },
  {
    key: "server_port",
    label: "Server Port",
    description: "Port the server listens on",
    category: PROPERTY_CATEGORIES.SERVER,
    type: "number",
    readOnly: true,
  },

  // GAMEPLAY SETTINGS
  {
    key: "gamemode",
    label: "Default Gamemode",
    description: "Default gamemode for new players",
    category: PROPERTY_CATEGORIES.GAMEPLAY,
    type: "select",
    options: GAMEMODE_OPTIONS as any,
    requiresRestart: true,
  },
  {
    key: "difficulty",
    label: "Difficulty",
    description: "Game difficulty level",
    category: PROPERTY_CATEGORIES.GAMEPLAY,
    type: "select",
    options: DIFFICULTY_OPTIONS as any,
    requiresRestart: true,
  },
  {
    key: "hardcore",
    label: "Hardcore Mode",
    description: "Players are banned on death in hardcore mode",
    category: PROPERTY_CATEGORIES.GAMEPLAY,
    type: "boolean",
    requiresRestart: true,
  },
  {
    key: "pvp",
    label: "PvP",
    description: "Enable player vs player combat",
    category: PROPERTY_CATEGORIES.GAMEPLAY,
    type: "boolean",
    requiresRestart: true,
  },

  // WORLD SETTINGS
  {
    key: "level_name",
    label: "World Name",
    description: "Name of the world folder",
    category: PROPERTY_CATEGORIES.WORLD,
    type: "string",
    readOnly: true,
  },
  {
    key: "level_seed",
    label: "World Seed",
    description: "Seed for world generation (empty for random)",
    category: PROPERTY_CATEGORIES.WORLD,
    type: "string",
    requiresWorldRegen: true,
    placeholder: "Leave empty for random",
  },
  {
    key: "level_type",
    label: "World Type",
    description: "Type of world to generate",
    category: PROPERTY_CATEGORIES.WORLD,
    type: "select",
    options: LEVEL_TYPE_OPTIONS as any,
    requiresWorldRegen: true,
  },
  {
    key: "generate_structures",
    label: "Generate Structures",
    description: "Generate villages, temples, etc.",
    category: PROPERTY_CATEGORIES.WORLD,
    type: "boolean",
    requiresWorldRegen: true,
  },
  {
    key: "spawn_monsters",
    label: "Spawn Monsters",
    description: "Allow hostile mobs to spawn",
    category: PROPERTY_CATEGORIES.WORLD,
    type: "boolean",
    requiresRestart: true,
  },
  {
    key: "spawn_animals",
    label: "Spawn Animals",
    description: "Allow passive mobs to spawn",
    category: PROPERTY_CATEGORIES.WORLD,
    type: "boolean",
    requiresRestart: true,
  },
  {
    key: "spawn_npcs",
    label: "Spawn Villagers",
    description: "Allow villagers to spawn",
    category: PROPERTY_CATEGORIES.WORLD,
    type: "boolean",
    requiresRestart: true,
  },

  // PERFORMANCE SETTINGS
  {
    key: "view_distance",
    label: "View Distance",
    description: "Maximum view distance in chunks (3-32)",
    category: PROPERTY_CATEGORIES.PERFORMANCE,
    type: "number",
    min: 3,
    max: 32,
    requiresRestart: true,
  },
  {
    key: "simulation_distance",
    label: "Simulation Distance",
    description: "Distance at which mobs/farms are active (3-32)",
    category: PROPERTY_CATEGORIES.PERFORMANCE,
    type: "number",
    min: 3,
    max: 32,
    requiresRestart: true,
  },
  {
    key: "max_tick_time",
    label: "Max Tick Time",
    description: "Maximum time per tick in milliseconds (-1 to disable watchdog)",
    category: PROPERTY_CATEGORIES.PERFORMANCE,
    type: "number",
    min: -1,
    requiresRestart: true,
  },

  // NETWORK SETTINGS
  {
    key: "online_mode",
    label: "Online Mode",
    description: "Authenticate players with Mojang servers",
    category: PROPERTY_CATEGORIES.NETWORK,
    type: "boolean",
    requiresRestart: true,
  },
  {
    key: "enable_status",
    label: "Enable Status",
    description: "Allow server to appear in server list",
    category: PROPERTY_CATEGORIES.NETWORK,
    type: "boolean",
    requiresRestart: true,
  },
  {
    key: "allow_flight",
    label: "Allow Flight",
    description: "Allow players to fly (required for some mods)",
    category: PROPERTY_CATEGORIES.NETWORK,
    type: "boolean",
    requiresRestart: true,
  },
  {
    key: "max_world_size",
    label: "Max World Size",
    description: "Maximum world border size",
    category: PROPERTY_CATEGORIES.NETWORK,
    type: "number",
    min: 1,
    max: 29999984,
    requiresRestart: true,
  },

  // SPAWN SETTINGS
  {
    key: "spawn_protection",
    label: "Spawn Protection",
    description: "Radius around spawn where only OPs can build",
    category: PROPERTY_CATEGORIES.SPAWN,
    type: "number",
    min: 0,
    requiresRestart: true,
  },
  {
    key: "force_gamemode",
    label: "Force Gamemode",
    description: "Force players to join in default gamemode",
    category: PROPERTY_CATEGORIES.SPAWN,
    type: "boolean",
    requiresRestart: true,
  },

  // WHITELIST & RESOURCE PACK
  {
    key: "white_list",
    label: "Enable Whitelist",
    description: "Only whitelisted players can join",
    category: PROPERTY_CATEGORIES.WHITELIST,
    type: "boolean",
    requiresRestart: true,
  },
  {
    key: "enforce_whitelist",
    label: "Enforce Whitelist",
    description: "Kick non-whitelisted players when enabled",
    category: PROPERTY_CATEGORIES.WHITELIST,
    type: "boolean",
    requiresRestart: true,
  },
  {
    key: "resource_pack",
    label: "Resource Pack URL",
    description: "URL to a resource pack",
    category: PROPERTY_CATEGORIES.WHITELIST,
    type: "string",
    requiresRestart: true,
    placeholder: "https://example.com/pack.zip",
  },
  {
    key: "resource_pack_prompt",
    label: "Resource Pack Message",
    description: "Optional message shown when prompting for resource pack",
    category: PROPERTY_CATEGORIES.WHITELIST,
    type: "string",
    requiresRestart: true,
    placeholder: "Please accept the resource pack",
  },
  {
    key: "require_resource_pack",
    label: "Require Resource Pack",
    description: "Kick players who decline the resource pack",
    category: PROPERTY_CATEGORIES.WHITELIST,
    type: "boolean",
    requiresRestart: true,
  },

  // COMMAND BLOCKS
  {
    key: "enable_command_block",
    label: "Enable Command Blocks",
    description: "Allow command blocks to function",
    category: PROPERTY_CATEGORIES.COMMAND_BLOCKS,
    type: "boolean",
    requiresRestart: true,
  },
  {
    key: "function_permission_level",
    label: "Function Permission Level",
    description: "Permission level required to run functions (1-4)",
    category: PROPERTY_CATEGORIES.COMMAND_BLOCKS,
    type: "number",
    min: 1,
    max: 4,
    requiresRestart: true,
  },
  {
    key: "op_permission_level",
    label: "OP Permission Level",
    description: "Default permission level for operators (1-4)",
    category: PROPERTY_CATEGORIES.COMMAND_BLOCKS,
    type: "number",
    min: 1,
    max: 4,
    requiresRestart: true,
  },

  // RCON SETTINGS (read-only)
  {
    key: "enable_rcon",
    label: "Enable RCON",
    description: "Enable RCON protocol for remote console access",
    category: PROPERTY_CATEGORIES.RCON,
    type: "boolean",
    readOnly: true,
  },
  {
    key: "rcon_port",
    label: "RCON Port",
    description: "Port for RCON connections",
    category: PROPERTY_CATEGORIES.RCON,
    type: "number",
    readOnly: true,
  },
  {
    key: "rcon_password",
    label: "RCON Password",
    description: "Password for RCON authentication",
    category: PROPERTY_CATEGORIES.RCON,
    type: "string",
    readOnly: true,
  },

  // QUERY SETTINGS
  {
    key: "enable_query",
    label: "Enable Query",
    description: "Enable GameSpy4 protocol server listener",
    category: PROPERTY_CATEGORIES.QUERY,
    type: "boolean",
    requiresRestart: true,
  },
  {
    key: "query_port",
    label: "Query Port",
    description: "Port for query protocol",
    category: PROPERTY_CATEGORIES.QUERY,
    type: "number",
    min: 1,
    max: 65535,
    requiresRestart: true,
  },
];
