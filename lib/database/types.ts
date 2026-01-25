/**
 * Database Types
 * 
 * TypeScript types generated from Supabase database schema.
 * These types are used for type-safe database operations.
 * 
 * Note: In production, these should be generated using:
 * npx supabase gen types typescript --local > lib/database/types.ts
 * 
 * For now, we define them manually based on the schema.
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      apps: {
        Row: {
          id: string
          name: string
          subdomain: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          name: string
          subdomain?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          name?: string
          subdomain?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      app_members: {
        Row: {
          id: string
          app_id: string
          user_id: string
          role: 'owner' | 'admin' | 'member'
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          app_id: string
          user_id: string
          role: 'owner' | 'admin' | 'member'
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          app_id?: string
          user_id?: string
          role?: 'owner' | 'admin' | 'member'
          created_at?: string
          updated_at?: string
        }
      }
      emails: {
        Row: {
          id: string
          app_id: string
          provider_id: string
          provider_type: 'gmail' | 'imap' | 'sendgrid' | 'mailgun' | 'microsoft_graph'
          thread_id: string | null
          sender_email: string
          sender_name: string | null
          subject: string | null
          body_text: string | null
          body_html: string | null
          received_at: string
          processed_at: string | null
          status: 'pending' | 'processing' | 'completed' | 'failed'
          provider_metadata: Json
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          app_id: string
          provider_id: string
          provider_type: 'gmail' | 'imap' | 'sendgrid' | 'mailgun' | 'microsoft_graph'
          thread_id?: string | null
          sender_email: string
          sender_name?: string | null
          subject?: string | null
          body_text?: string | null
          body_html?: string | null
          received_at: string
          processed_at?: string | null
          status?: 'pending' | 'processing' | 'completed' | 'failed'
          provider_metadata?: Json
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          app_id?: string
          provider_id?: string
          provider_type?: 'gmail' | 'imap' | 'sendgrid' | 'mailgun' | 'microsoft_graph'
          thread_id?: string | null
          sender_email?: string
          sender_name?: string | null
          subject?: string | null
          body_text?: string | null
          body_html?: string | null
          received_at?: string
          processed_at?: string | null
          status?: 'pending' | 'processing' | 'completed' | 'failed'
          provider_metadata?: Json
          created_at?: string
          updated_at?: string
        }
      }
      document_chunks: {
        Row: {
          id: string
          app_id: string
          email_id: string
          attachment_id: string | null
          chunk_index: number
          content: string
          embedding: number[] | null
          token_count: number | null
          metadata: Json
          created_at: string
        }
        Insert: {
          id?: string
          app_id: string
          email_id: string
          attachment_id?: string | null
          chunk_index: number
          content: string
          embedding?: number[] | null
          token_count?: number | null
          metadata?: Json
          created_at?: string
        }
        Update: {
          id?: string
          app_id?: string
          email_id?: string
          attachment_id?: string | null
          chunk_index?: number
          content?: string
          embedding?: number[] | null
          token_count?: number | null
          metadata?: Json
          created_at?: string
        }
      }
      // Add other tables as needed...
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}
