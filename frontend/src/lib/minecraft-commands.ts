/**
 * Minecraft server commands with syntax and descriptions
 */

export interface MinecraftCommand {
  command: string;
  syntax: string;
  description: string;
  aliases?: string[];
  category: "admin" | "gameplay" | "teleport" | "world" | "info";
}

export const MINECRAFT_COMMANDS: MinecraftCommand[] = [
  // Admin commands
  {
    command: "ban",
    syntax: "ban <player> [reason]",
    description: "Ban a player from the server",
    category: "admin",
  },
  {
    command: "ban-ip",
    syntax: "ban-ip <ip|player> [reason]",
    description: "Ban an IP address",
    category: "admin",
  },
  {
    command: "pardon",
    syntax: "pardon <player>",
    description: "Remove a player from the ban list",
    category: "admin",
  },
  {
    command: "pardon-ip",
    syntax: "pardon-ip <ip>",
    description: "Remove an IP from the ban list",
    category: "admin",
  },
  {
    command: "kick",
    syntax: "kick <player> [reason]",
    description: "Kick a player from the server",
    category: "admin",
  },
  {
    command: "op",
    syntax: "op <player>",
    description: "Grant operator status to a player",
    category: "admin",
  },
  {
    command: "deop",
    syntax: "deop <player>",
    description: "Remove operator status from a player",
    category: "admin",
  },
  {
    command: "whitelist",
    syntax: "whitelist <add|remove|list|on|off|reload> [player]",
    description: "Manage server whitelist",
    category: "admin",
  },

  // Gameplay commands
  {
    command: "gamemode",
    syntax: "gamemode <survival|creative|adventure|spectator> [player]",
    description: "Change game mode for a player",
    aliases: ["gm"],
    category: "gameplay",
  },
  {
    command: "difficulty",
    syntax: "difficulty <peaceful|easy|normal|hard>",
    description: "Set the difficulty level",
    category: "gameplay",
  },
  {
    command: "give",
    syntax: "give <player> <item> [amount]",
    description: "Give an item to a player",
    category: "gameplay",
  },
  {
    command: "clear",
    syntax: "clear [player] [item] [maxCount]",
    description: "Clear items from player inventory",
    category: "gameplay",
  },
  {
    command: "effect",
    syntax: "effect <give|clear> <player> [effect] [duration] [amplifier]",
    description: "Apply or remove status effects",
    category: "gameplay",
  },
  {
    command: "enchant",
    syntax: "enchant <player> <enchantment> [level]",
    description: "Enchant a player's item",
    category: "gameplay",
  },
  {
    command: "xp",
    syntax: "xp <add|set|query> <player> <amount> [levels|points]",
    description: "Manage player experience",
    aliases: ["experience"],
    category: "gameplay",
  },

  // Teleport commands
  {
    command: "tp",
    syntax: "tp [player] <destination|x y z>",
    description: "Teleport players",
    aliases: ["teleport"],
    category: "teleport",
  },
  {
    command: "spawnpoint",
    syntax: "spawnpoint [player] [x y z]",
    description: "Set spawn point for a player",
    category: "teleport",
  },
  {
    command: "setworldspawn",
    syntax: "setworldspawn [x y z]",
    description: "Set the world spawn point",
    category: "teleport",
  },

  // World commands
  {
    command: "time",
    syntax: "time <set|add> <value>",
    description: "Change or query the world time",
    category: "world",
  },
  {
    command: "weather",
    syntax: "weather <clear|rain|thunder> [duration]",
    description: "Set the weather",
    category: "world",
  },
  {
    command: "gamerule",
    syntax: "gamerule <rule> [value]",
    description: "Set or query game rules",
    category: "world",
  },
  {
    command: "seed",
    syntax: "seed",
    description: "Display the world seed",
    category: "world",
  },
  {
    command: "fill",
    syntax: "fill <from x y z> <to x y z> <block>",
    description: "Fill a region with blocks",
    category: "world",
  },
  {
    command: "setblock",
    syntax: "setblock <x y z> <block>",
    description: "Change a block",
    category: "world",
  },

  // Info commands
  {
    command: "list",
    syntax: "list [uuids]",
    description: "List online players",
    category: "info",
  },
  {
    command: "help",
    syntax: "help [command]",
    description: "Display help for commands",
    category: "info",
  },
  {
    command: "say",
    syntax: "say <message>",
    description: "Send a message to all players",
    category: "info",
  },
  {
    command: "msg",
    syntax: "msg <player> <message>",
    description: "Send a private message",
    aliases: ["tell", "w"],
    category: "info",
  },
  {
    command: "save-all",
    syntax: "save-all [flush]",
    description: "Save the server to disk",
    category: "admin",
  },
  {
    command: "save-on",
    syntax: "save-on",
    description: "Enable automatic saving",
    category: "admin",
  },
  {
    command: "save-off",
    syntax: "save-off",
    description: "Disable automatic saving",
    category: "admin",
  },
  {
    command: "stop",
    syntax: "stop",
    description: "Stop the server gracefully",
    category: "admin",
  },
];

/**
 * Extract parameter options from syntax string
 * Example: "gamemode <survival|creative|adventure|spectator> [player]"
 * Returns: ["survival", "creative", "adventure", "spectator"] for position 1
 */
function extractParameterOptions(syntax: string, paramPosition: number): string[] {
  // Remove command name
  const parts = syntax.split(/\s+/).slice(1);

  if (paramPosition >= parts.length) return [];

  const param = parts[paramPosition];

  // Extract options from <option1|option2|option3> format
  const optionsMatch = param.match(/<([^>]+)>/);
  if (optionsMatch) {
    return optionsMatch[1].split("|");
  }

  return [];
}

/**
 * Get suggestions based on user input
 */
export function getCommandSuggestions(
  input: string,
  playerNames: string[] = []
): Array<{ type: "command" | "player" | "syntax" | "param"; text: string; detail: string; completionText: string }> {
  const trimmedInput = input.trim();

  // Empty input - show common commands
  if (!trimmedInput) {
    return MINECRAFT_COMMANDS.slice(0, 10).map((cmd) => ({
      type: "command" as const,
      text: cmd.command,
      detail: cmd.description,
      completionText: cmd.command,
    }));
  }

  const suggestions: Array<{ type: "command" | "player" | "syntax" | "param"; text: string; detail: string; completionText: string }> = [];

  // Parse input to detect if we're completing a command or a parameter
  const parts = trimmedInput.split(/\s+/);
  const commandPart = parts[0].toLowerCase();

  // First word - suggest commands
  if (parts.length === 1) {
    // Match command names and aliases
    const matchingCommands = MINECRAFT_COMMANDS.filter((cmd) => {
      return (
        cmd.command.toLowerCase().startsWith(commandPart) ||
        cmd.aliases?.some((alias) => alias.toLowerCase().startsWith(commandPart))
      );
    });

    suggestions.push(
      ...matchingCommands.map((cmd) => ({
        type: "command" as const,
        text: cmd.command,
        detail: cmd.description,
        completionText: cmd.command,
      }))
    );
  } else {
    // Completing parameters - show syntax hint first
    const currentCommand = MINECRAFT_COMMANDS.find(
      (cmd) =>
        cmd.command.toLowerCase() === commandPart ||
        cmd.aliases?.some((alias) => alias.toLowerCase() === commandPart)
    );

    if (currentCommand) {
      suggestions.push({
        type: "syntax" as const,
        text: currentCommand.syntax,
        detail: currentCommand.description,
        completionText: "", // Don't complete, just show as reference
      });

      // Extract valid options for current parameter position
      const paramPosition = parts.length - 2; // -1 for command, -1 for 0-indexed
      const paramOptions = extractParameterOptions(currentCommand.syntax, paramPosition);

      const currentParam = parts[parts.length - 1].toLowerCase();

      // Suggest parameter options that match
      if (paramOptions.length > 0) {
        const matchingOptions = paramOptions.filter((option) =>
          option.toLowerCase().startsWith(currentParam)
        );

        suggestions.push(
          ...matchingOptions.map((option) => ({
            type: "param" as const,
            text: option,
            detail: `${currentCommand.command} parameter`,
            completionText: option,
          }))
        );
      }
    }

    // Suggest player names if applicable
    const currentParam = parts[parts.length - 1].toLowerCase();

    // Only suggest players if there's a partial match or empty last part
    if (currentParam || parts[parts.length - 1] === "") {
      const matchingPlayers = playerNames.filter((name) =>
        name.toLowerCase().startsWith(currentParam)
      );

      suggestions.push(
        ...matchingPlayers.map((name) => ({
          type: "player" as const,
          text: name,
          detail: "Online player",
          completionText: name,
        }))
      );
    }
  }

  return suggestions.slice(0, 8); // Limit to 8 suggestions
}
