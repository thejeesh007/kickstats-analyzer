-- Create teams table
CREATE TABLE public.teams (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    league TEXT NOT NULL,
    founded INTEGER,
    stadium TEXT,
    coach TEXT,
    logo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create players table
CREATE TABLE public.players (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    team_id UUID REFERENCES public.teams(id) ON DELETE SET NULL,
    position TEXT NOT NULL,
    jersey_number INTEGER,
    age INTEGER,
    nationality TEXT,
    market_value DECIMAL(15,2),
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    matches_played INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create matches table
CREATE TABLE public.matches (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    home_team_id UUID NOT NULL REFERENCES public.teams(id),
    away_team_id UUID NOT NULL REFERENCES public.teams(id),
    match_date TIMESTAMP WITH TIME ZONE NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status TEXT NOT NULL DEFAULT 'scheduled', -- scheduled, live, completed, postponed
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create match_predictions table
CREATE TABLE public.match_predictions (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    match_id UUID NOT NULL REFERENCES public.matches(id) ON DELETE CASCADE,
    predicted_home_score DECIMAL(3,2),
    predicted_away_score DECIMAL(3,2),
    home_win_probability DECIMAL(5,2),
    draw_probability DECIMAL(5,2),
    away_win_probability DECIMAL(5,2),
    key_factors TEXT[],
    ai_analysis TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS on all tables
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.players ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_predictions ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (since this is sports data)
CREATE POLICY "Anyone can view teams" ON public.teams FOR SELECT USING (true);
CREATE POLICY "Anyone can view players" ON public.players FOR SELECT USING (true);
CREATE POLICY "Anyone can view matches" ON public.matches FOR SELECT USING (true);
CREATE POLICY "Anyone can view predictions" ON public.match_predictions FOR SELECT USING (true);

-- Admin policies for data management (only authenticated users can modify)
CREATE POLICY "Authenticated users can insert teams" ON public.teams FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Authenticated users can update teams" ON public.teams FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Authenticated users can delete teams" ON public.teams FOR DELETE TO authenticated USING (true);

CREATE POLICY "Authenticated users can insert players" ON public.players FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Authenticated users can update players" ON public.players FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Authenticated users can delete players" ON public.players FOR DELETE TO authenticated USING (true);

CREATE POLICY "Authenticated users can insert matches" ON public.matches FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Authenticated users can update matches" ON public.matches FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Authenticated users can delete matches" ON public.matches FOR DELETE TO authenticated USING (true);

CREATE POLICY "Authenticated users can insert predictions" ON public.match_predictions FOR INSERT TO authenticated WITH CHECK (true);

-- Add update triggers
CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON public.teams
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_players_updated_at
    BEFORE UPDATE ON public.players
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_matches_updated_at
    BEFORE UPDATE ON public.matches
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();