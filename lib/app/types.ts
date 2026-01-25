/**
 * App Types
 * 
 * Type definitions for multi-tenant app system.
 */

export interface App {
  id: string;
  name: string;
  subdomain: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppMember {
  id: string;
  app_id: string;
  user_id: string;
  role: 'owner' | 'admin' | 'member';
  created_at: string;
  updated_at: string;
}

export interface AppConfig {
  id: string;
  app_id: string;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AppWithConfig extends App {
  config?: AppConfig['config'];
}
