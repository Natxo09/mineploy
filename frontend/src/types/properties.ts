/**
 * Server properties types
 */

export type Gamemode = "survival" | "creative" | "adventure" | "spectator";
export type Difficulty = "peaceful" | "easy" | "normal" | "hard";
export type LevelType =
  | "default"
  | "flat"
  | "largeBiomes"
  | "amplified"
  | "buffet"
  | "minecraft:normal"
  | "minecraft:flat"
  | "minecraft:large_biomes"
  | "minecraft:amplified";

/**
 * Server properties response (all fields required)
 */
export interface ServerProperties {
  // Server settings
  motd: string;
  max_players: number;
  server_port: number;

  // Gameplay settings
  gamemode: Gamemode;
  difficulty: Difficulty;
  hardcore: boolean;
  pvp: boolean;

  // World settings
  level_name: string;
  level_seed: string;
  level_type: LevelType;
  generate_structures: boolean;
  spawn_monsters: boolean;
  spawn_animals: boolean;
  spawn_npcs: boolean;

  // Performance settings
  view_distance: number;
  simulation_distance: number;
  max_tick_time: number;

  // Network settings
  online_mode: boolean;
  enable_status: boolean;
  allow_flight: boolean;
  max_world_size: number;

  // Spawn settings
  spawn_protection: number;
  force_gamemode: boolean;

  // Other settings
  white_list: boolean;
  enforce_whitelist: boolean;
  resource_pack: string;
  resource_pack_prompt: string;
  require_resource_pack: boolean;
  enable_command_block: boolean;
  function_permission_level: number;
  op_permission_level: number;

  // RCON settings
  enable_rcon: boolean;
  rcon_port: number;
  rcon_password: string;

  // Query settings
  enable_query: boolean;
  query_port: number;
}

/**
 * Update server properties request (all fields optional)
 */
export interface UpdateServerPropertiesRequest {
  // Server settings
  motd?: string;
  max_players?: number;

  // Gameplay settings
  gamemode?: Gamemode;
  difficulty?: Difficulty;
  hardcore?: boolean;
  pvp?: boolean;

  // World settings
  level_seed?: string;
  level_type?: LevelType;
  generate_structures?: boolean;
  spawn_monsters?: boolean;
  spawn_animals?: boolean;
  spawn_npcs?: boolean;

  // Performance settings
  view_distance?: number;
  simulation_distance?: number;
  max_tick_time?: number;

  // Network settings
  online_mode?: boolean;
  enable_status?: boolean;
  allow_flight?: boolean;
  max_world_size?: number;

  // Spawn settings
  spawn_protection?: number;
  force_gamemode?: boolean;

  // Other settings
  white_list?: boolean;
  enforce_whitelist?: boolean;
  resource_pack?: string;
  resource_pack_prompt?: string;
  require_resource_pack?: boolean;
  enable_command_block?: boolean;
  function_permission_level?: number;
  op_permission_level?: number;

  // Query settings
  enable_query?: boolean;
}

/**
 * Property categories for UI organization
 */
export const PROPERTY_CATEGORIES = {
  SERVER: "Server",
  GAMEPLAY: "Gameplay",
  WORLD: "World",
  PERFORMANCE: "Performance",
  NETWORK: "Network",
  SPAWN: "Spawn",
  WHITELIST: "Whitelist & Resource Pack",
  COMMAND_BLOCKS: "Command Blocks",
  RCON: "RCON",
  QUERY: "Query",
} as const;

export type PropertyCategory =
  (typeof PROPERTY_CATEGORIES)[keyof typeof PROPERTY_CATEGORIES];

/**
 * Property metadata for form generation
 */
export interface PropertyMetadata {
  key: keyof ServerProperties;
  label: string;
  description: string;
  category: PropertyCategory;
  type: "string" | "number" | "boolean" | "select";
  options?: readonly string[];
  min?: number;
  max?: number;
  step?: number;
  readOnly?: boolean;
  requiresRestart?: boolean;
  requiresWorldRegen?: boolean;
}

/**
 * Gamemode options
 */
export const GAMEMODE_OPTIONS: readonly Gamemode[] = [
  "survival",
  "creative",
  "adventure",
  "spectator",
] as const;

/**
 * Difficulty options
 */
export const DIFFICULTY_OPTIONS: readonly Difficulty[] = [
  "peaceful",
  "easy",
  "normal",
  "hard",
] as const;

/**
 * Level type options
 */
export const LEVEL_TYPE_OPTIONS: readonly LevelType[] = [
  "default",
  "flat",
  "largeBiomes",
  "amplified",
  "buffet",
] as const;
