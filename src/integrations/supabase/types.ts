export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "13.0.4"
  }
  public: {
    Tables: {
      match_predictions: {
        Row: {
          ai_analysis: string | null
          away_win_probability: number | null
          created_at: string
          draw_probability: number | null
          home_win_probability: number | null
          id: string
          key_factors: string[] | null
          match_id: string
          predicted_away_score: number | null
          predicted_home_score: number | null
        }
        Insert: {
          ai_analysis?: string | null
          away_win_probability?: number | null
          created_at?: string
          draw_probability?: number | null
          home_win_probability?: number | null
          id?: string
          key_factors?: string[] | null
          match_id: string
          predicted_away_score?: number | null
          predicted_home_score?: number | null
        }
        Update: {
          ai_analysis?: string | null
          away_win_probability?: number | null
          created_at?: string
          draw_probability?: number | null
          home_win_probability?: number | null
          id?: string
          key_factors?: string[] | null
          match_id?: string
          predicted_away_score?: number | null
          predicted_home_score?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "match_predictions_match_id_fkey"
            columns: ["match_id"]
            isOneToOne: false
            referencedRelation: "matches"
            referencedColumns: ["id"]
          },
        ]
      }
      matches: {
        Row: {
          away_score: number | null
          away_team_id: string
          created_at: string
          home_score: number | null
          home_team_id: string
          id: string
          league: string
          match_date: string
          season: string
          status: string
          updated_at: string
        }
        Insert: {
          away_score?: number | null
          away_team_id: string
          created_at?: string
          home_score?: number | null
          home_team_id: string
          id?: string
          league: string
          match_date: string
          season: string
          status?: string
          updated_at?: string
        }
        Update: {
          away_score?: number | null
          away_team_id?: string
          created_at?: string
          home_score?: number | null
          home_team_id?: string
          id?: string
          league?: string
          match_date?: string
          season?: string
          status?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "matches_away_team_id_fkey"
            columns: ["away_team_id"]
            isOneToOne: false
            referencedRelation: "teams"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "matches_home_team_id_fkey"
            columns: ["home_team_id"]
            isOneToOne: false
            referencedRelation: "teams"
            referencedColumns: ["id"]
          },
        ]
      }
      players: {
        Row: {
          age: number | null
          assists: number | null
          created_at: string
          goals: number | null
          id: string
          jersey_number: number | null
          market_value: number | null
          matches_played: number | null
          name: string
          nationality: string | null
          position: string
          red_cards: number | null
          team_id: string | null
          updated_at: string
          yellow_cards: number | null
        }
        Insert: {
          age?: number | null
          assists?: number | null
          created_at?: string
          goals?: number | null
          id?: string
          jersey_number?: number | null
          market_value?: number | null
          matches_played?: number | null
          name: string
          nationality?: string | null
          position: string
          red_cards?: number | null
          team_id?: string | null
          updated_at?: string
          yellow_cards?: number | null
        }
        Update: {
          age?: number | null
          assists?: number | null
          created_at?: string
          goals?: number | null
          id?: string
          jersey_number?: number | null
          market_value?: number | null
          matches_played?: number | null
          name?: string
          nationality?: string | null
          position?: string
          red_cards?: number | null
          team_id?: string | null
          updated_at?: string
          yellow_cards?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "players_team_id_fkey"
            columns: ["team_id"]
            isOneToOne: false
            referencedRelation: "teams"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          coach_experience: number | null
          coach_license: string | null
          coach_team: string | null
          created_at: string
          email: string
          id: string
          name: string
          player_jersey_number: number | null
          player_position: string | null
          player_team: string | null
          role: string
          updated_at: string
        }
        Insert: {
          coach_experience?: number | null
          coach_license?: string | null
          coach_team?: string | null
          created_at?: string
          email: string
          id: string
          name: string
          player_jersey_number?: number | null
          player_position?: string | null
          player_team?: string | null
          role: string
          updated_at?: string
        }
        Update: {
          coach_experience?: number | null
          coach_license?: string | null
          coach_team?: string | null
          created_at?: string
          email?: string
          id?: string
          name?: string
          player_jersey_number?: number | null
          player_position?: string | null
          player_team?: string | null
          role?: string
          updated_at?: string
        }
        Relationships: []
      }
      teams: {
        Row: {
          coach: string | null
          created_at: string
          founded: number | null
          id: string
          league: string
          logo_url: string | null
          name: string
          stadium: string | null
          updated_at: string
        }
        Insert: {
          coach?: string | null
          created_at?: string
          founded?: number | null
          id?: string
          league: string
          logo_url?: string | null
          name: string
          stadium?: string | null
          updated_at?: string
        }
        Update: {
          coach?: string | null
          created_at?: string
          founded?: number | null
          id?: string
          league?: string
          logo_url?: string | null
          name?: string
          stadium?: string | null
          updated_at?: string
        }
        Relationships: []
      }
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
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
