/**
 * Setup wizard types
 */

export interface SetupRequest {
  username: string;
  email: string;
  password: string;
}

export interface SetupResponse {
  success: boolean;
  message: string;
  admin_username: string;
  next_steps: string[];
}

export interface SetupStatus {
  setup_completed: boolean;
  requires_setup: boolean;
  message: string;
}
