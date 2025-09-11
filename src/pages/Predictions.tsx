import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import Navigation from '@/components/Navigation';
import { Target, Brain, TrendingUp, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';

type Match = {
  id: string;
  match_date: string;
  home_team?: { name: string };
  away_team?: { name: string };
  league: string;
  status: string;
};

type Prediction = {
  id: string;
  match_id: string;
  predicted_home_score: number;
  predicted_away_score: number;
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
  key_factors: string[];
  ai_analysis: string;
  created_at: string;
  matches: Match;
};

const Predictions = () => {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [upcomingMatches, setUpcomingMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [generatingPrediction, setGeneratingPrediction] = useState<string | null>(null);

  useEffect(() => {
    fetchPredictions();
    fetchUpcomingMatches();
  }, []);

  const fetchPredictions = async () => {
    try {
      const { data, error } = await supabase
        .from('match_predictions')
        .select(`
          *,
          matches (
            id,
            match_date,
            league,
            status,
            home_team:teams!matches_home_team_id_fkey (name),
            away_team:teams!matches_away_team_id_fkey (name)
          )
        `)
        .order('created_at', { ascending: false });

      if (error) throw error;
      setPredictions(data || []);
    } catch (error) {
      console.error('Error fetching predictions:', error);
    }
  };

  const fetchUpcomingMatches = async () => {
    try {
      const { data, error } = await supabase
        .from('matches')
        .select(`
          id,
          match_date,
          league,
          status,
          home_team:teams!matches_home_team_id_fkey (name),
          away_team:teams!matches_away_team_id_fkey (name)
        `)
        .eq('status', 'scheduled')
        .order('match_date', { ascending: true })
        .limit(10);

      if (error) throw error;
      
      // Filter out matches that already have predictions
      const predictedMatchIds = new Set(predictions.map(p => p.match_id));
      const unpredictedMatches = (data || []).filter(match => !predictedMatchIds.has(match.id));
      
      setUpcomingMatches(unpredictedMatches);
    } catch (error) {
      console.error('Error fetching upcoming matches:', error);
    } finally {
      setLoading(false);
    }
  };

  const generatePrediction = async (match: Match) => {
    setGeneratingPrediction(match.id);
    
    try {
      // Mock AI prediction generation - in a real app, this would call an AI service
      const mockPrediction = {
        match_id: match.id,
        predicted_home_score: Number((Math.random() * 3 + 0.5).toFixed(2)),
        predicted_away_score: Number((Math.random() * 3 + 0.5).toFixed(2)),
        home_win_probability: Number((Math.random() * 40 + 30).toFixed(2)),
        draw_probability: Number((Math.random() * 30 + 20).toFixed(2)),
        away_win_probability: Number((Math.random() * 40 + 30).toFixed(2)),
        key_factors: [
          'Home advantage',
          'Recent form comparison',
          'Head-to-head record',
          'Player availability'
        ],
        ai_analysis: `Based on current form, recent performances, and historical data, this match presents an interesting tactical battle. The home team's recent attacking prowess will be tested against the away team's solid defensive structure. Key players' fitness and weather conditions may play decisive roles in the outcome.`
      };

      const { error } = await supabase
        .from('match_predictions')
        .insert(mockPrediction);

      if (error) throw error;

      // Refresh predictions and upcoming matches
      await fetchPredictions();
      await fetchUpcomingMatches();
    } catch (error) {
      console.error('Error generating prediction:', error);
    } finally {
      setGeneratingPrediction(null);
    }
  };

  const getMostLikelyOutcome = (prediction: Prediction) => {
    const { home_win_probability, draw_probability, away_win_probability } = prediction;
    const max = Math.max(home_win_probability, draw_probability, away_win_probability);
    
    if (max === home_win_probability) return 'Home Win';
    if (max === away_win_probability) return 'Away Win';
    return 'Draw';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto p-6 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading predictions...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Match Predictions</h1>
          <p className="text-muted-foreground">AI-powered football match predictions and analysis</p>
        </div>

        {upcomingMatches.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Generate New Predictions
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {upcomingMatches.slice(0, 6).map((match) => (
                <Card key={match.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="text-center space-y-3">
                      <div className="flex items-center justify-between text-sm font-medium">
                        <span>{match.home_team?.name || 'TBD'}</span>
                        <span className="text-muted-foreground">vs</span>
                        <span>{match.away_team?.name || 'TBD'}</span>
                      </div>
                      
                      <div className="text-xs text-muted-foreground">
                        {format(new Date(match.match_date), 'MMM dd, yyyy HH:mm')}
                      </div>
                      
                      <Button 
                        onClick={() => generatePrediction(match)}
                        disabled={generatingPrediction === match.id}
                        className="w-full"
                        size="sm"
                      >
                        {generatingPrediction === match.id ? (
                          <>
                            <div className="animate-spin rounded-full h-3 w-3 border-b border-white mr-2"></div>
                            Analyzing...
                          </>
                        ) : (
                          <>
                            <Brain className="w-3 h-3 mr-2" />
                            Generate Prediction
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
            <Target className="w-5 h-5" />
            Latest Predictions
          </h2>
          
          <div className="space-y-6">
            {predictions.map((prediction) => (
              <Card key={prediction.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <span className="text-lg">
                        {prediction.matches.home_team?.name} vs {prediction.matches.away_team?.name}
                      </span>
                      <Badge variant="secondary">{prediction.matches.league}</Badge>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      <TrendingUp className="w-3 h-3 mr-1" />
                      {getMostLikelyOutcome(prediction)}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold mb-3">Predicted Score</h4>
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <div className="text-2xl font-bold">
                          {prediction.predicted_home_score.toFixed(1)} - {prediction.predicted_away_score.toFixed(1)}
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold mb-3">Win Probabilities</h4>
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Home Win</span>
                            <span>{prediction.home_win_probability}%</span>
                          </div>
                          <Progress value={prediction.home_win_probability} className="h-2" />
                        </div>
                        
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Draw</span>
                            <span>{prediction.draw_probability}%</span>
                          </div>
                          <Progress value={prediction.draw_probability} className="h-2" />
                        </div>
                        
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Away Win</span>
                            <span>{prediction.away_win_probability}%</span>
                          </div>
                          <Progress value={prediction.away_win_probability} className="h-2" />
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-3">Key Factors</h4>
                    <div className="flex flex-wrap gap-2">
                      {prediction.key_factors?.map((factor, index) => (
                        <Badge key={index} variant="outline">
                          {factor}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-3">AI Analysis</h4>
                    <p className="text-muted-foreground leading-relaxed">
                      {prediction.ai_analysis}
                    </p>
                  </div>
                  
                  <div className="text-xs text-muted-foreground border-t pt-3">
                    Prediction generated on {format(new Date(prediction.created_at), 'MMM dd, yyyy HH:mm')}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {predictions.length === 0 && upcomingMatches.length === 0 && (
          <div className="text-center py-12">
            <Target className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground text-lg">No predictions available yet.</p>
            <p className="text-sm text-muted-foreground">Add some matches to generate predictions.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Predictions;