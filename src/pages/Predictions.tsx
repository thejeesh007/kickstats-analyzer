import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Brain, TrendingUp, Target, Sparkles } from "lucide-react";

interface PredictionResult {
  predicted_home_score: number;
  predicted_away_score: number;
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
  key_factors: string[];
  ai_analysis: string;
}

const Predictions = () => {
  const [teams, setTeams] = useState<string[]>([]);
  const [homeTeam, setHomeTeam] = useState("");
  const [awayTeam, setAwayTeam] = useState("");
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch available teams from FastAPI
  const fetchTeams = async () => {
    try {
      const res = await axios.get("http://localhost:8000/teams");
      setTeams(res.data.teams || []);
    } catch (err) {
      console.error("Error fetching teams:", err);
      setError("Unable to load team list. Make sure backend is running.");
    }
  };

  useEffect(() => {
    fetchTeams();
  }, []);

  const handlePredict = async () => {
    if (!homeTeam || !awayTeam) {
      setError("Please select both teams.");
      return;
    }
    if (homeTeam === awayTeam) {
      setError("Home and Away teams must be different.");
      return;
    }

    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const response = await axios.post("http://localhost:8000/predict", {
        home_team: homeTeam,
        away_team: awayTeam,
      });
      setPrediction(response.data);
    } catch (err: any) {
      console.error("Prediction error:", err);
      setError(
        err.response?.data?.detail ||
          "Failed to generate prediction. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const getWinnerInfo = () => {
    if (!prediction) return null;
    const { home_win_probability, draw_probability, away_win_probability } = prediction;
    
    if (home_win_probability > draw_probability && home_win_probability > away_win_probability) {
      return { team: homeTeam, prob: home_win_probability, type: 'home' };
    } else if (away_win_probability > draw_probability && away_win_probability > home_win_probability) {
      return { team: awayTeam, prob: away_win_probability, type: 'away' };
    }
    return { team: 'Draw', prob: draw_probability, type: 'draw' };
  };

  const winner = getWinnerInfo();

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-900 to-slate-900 py-12 px-4">
      <div className="container mx-auto max-w-5xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full mb-4 shadow-2xl">
            <Brain className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-5xl font-extrabold text-white mb-3 tracking-tight">
            AI Match Predictor
          </h1>
          <p className="text-purple-200 text-lg">Advanced machine learning powered predictions</p>
        </div>

        <div className="grid md:grid-cols-5 gap-6">
          {/* Selection Panel */}
          <Card className="md:col-span-2 bg-white/95 backdrop-blur border-0 shadow-2xl">
            <CardHeader className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-t-xl">
              <CardTitle className="text-2xl font-bold flex items-center gap-2">
                <Target className="w-6 h-6" />
                Select Teams
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-6 pt-6">
              <div>
                <label className="block mb-3 text-sm font-bold text-gray-700 uppercase tracking-wide">
                  🏠 Home Team
                </label>
                <select
                  value={homeTeam}
                  onChange={(e) => setHomeTeam(e.target.value)}
                  className="w-full border-2 border-gray-300 focus:border-blue-500 rounded-xl px-4 py-3 text-gray-800 font-medium transition outline-none bg-gradient-to-r from-blue-50 to-white"
                >
                  <option value="">-- Choose Home Team --</option>
                  {teams.map((team) => (
                    <option key={team} value={team}>
                      {team}
                    </option>
                  ))}
                </select>
              </div>

              <div className="text-center text-2xl font-bold text-gray-400">VS</div>

              <div>
                <label className="block mb-3 text-sm font-bold text-gray-700 uppercase tracking-wide">
                  ✈️ Away Team
                </label>
                <select
                  value={awayTeam}
                  onChange={(e) => setAwayTeam(e.target.value)}
                  className="w-full border-2 border-gray-300 focus:border-purple-500 rounded-xl px-4 py-3 text-gray-800 font-medium transition outline-none bg-gradient-to-r from-purple-50 to-white"
                >
                  <option value="">-- Choose Away Team --</option>
                  {teams.map((team) => (
                    <option key={team} value={team}>
                      {team}
                    </option>
                  ))}
                </select>
              </div>

              <Button
                onClick={handlePredict}
                disabled={loading || !homeTeam || !awayTeam}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 font-bold text-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105 active:scale-95"
              >
                {loading ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Analyzing...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <Sparkles className="w-5 h-5" />
                    <span>Predict Match</span>
                  </div>
                )}
              </Button>

              {error && (
                <div className="bg-red-50 border-2 border-red-300 text-red-700 px-4 py-3 rounded-xl text-center font-semibold">
                  ⚠️ {error}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Results Panel */}
          <div className="md:col-span-3 space-y-6">
            {prediction ? (
              <>
                {/* Score Prediction */}
                <Card className="bg-gradient-to-br from-white to-blue-50 border-0 shadow-2xl overflow-hidden">
                  <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
                    <h3 className="text-2xl font-bold mb-4 flex items-center gap-2">
                      <TrendingUp className="w-6 h-6" />
                      Predicted Score
                    </h3>
                    <div className="flex items-center justify-between">
                      <div className="text-center flex-1">
                        <div className="text-lg font-semibold mb-2 opacity-90">{homeTeam}</div>
                        <div className="text-6xl font-black">{prediction.predicted_home_score.toFixed(1)}</div>
                      </div>
                      <div className="text-4xl font-bold px-6">-</div>
                      <div className="text-center flex-1">
                        <div className="text-lg font-semibold mb-2 opacity-90">{awayTeam}</div>
                        <div className="text-6xl font-black">{prediction.predicted_away_score.toFixed(1)}</div>
                      </div>
                    </div>
                  </div>
                  
                  {winner && (
                    <div className="p-4 bg-gradient-to-r from-yellow-400 to-orange-400 text-center">
                      <div className="text-white font-bold text-lg">
                        🏆 Predicted Winner: <span className="text-xl">{winner.team}</span> ({winner.prob.toFixed(1)}%)
                      </div>
                    </div>
                  )}
                </Card>

                {/* Win Probabilities */}
                <Card className="bg-white/95 backdrop-blur border-0 shadow-2xl">
                  <CardHeader>
                    <CardTitle className="text-xl font-bold text-gray-800">Match Outcome Probabilities</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm font-semibold mb-2">
                        <span className="text-blue-700">🏠 {homeTeam} Win</span>
                        <span className="text-blue-700">{prediction.home_win_probability.toFixed(1)}%</span>
                      </div>
                      <Progress value={prediction.home_win_probability} className="h-3 bg-blue-100" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm font-semibold mb-2">
                        <span className="text-gray-700">🤝 Draw</span>
                        <span className="text-gray-700">{prediction.draw_probability.toFixed(1)}%</span>
                      </div>
                      <Progress value={prediction.draw_probability} className="h-3 bg-gray-100" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm font-semibold mb-2">
                        <span className="text-purple-700">✈️ {awayTeam} Win</span>
                        <span className="text-purple-700">{prediction.away_win_probability.toFixed(1)}%</span>
                      </div>
                      <Progress value={prediction.away_win_probability} className="h-3 bg-purple-100" />
                    </div>
                  </CardContent>
                </Card>

                {/* Key Factors */}
                <Card className="bg-white/95 backdrop-blur border-0 shadow-2xl">
                  <CardHeader className="bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-t-xl">
                    <CardTitle className="text-xl font-bold">🎯 Key Factors</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <div className="grid gap-3">
                      {prediction.key_factors.map((factor, i) => (
                        <div key={i} className="flex items-start gap-3 bg-gradient-to-r from-green-50 to-teal-50 p-4 rounded-lg border border-green-200">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500 text-white flex items-center justify-center text-xs font-bold">
                            {i + 1}
                          </div>
                          <p className="text-gray-800 font-medium">{factor}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* AI Analysis */}
                <Card className="bg-gradient-to-br from-purple-900 to-indigo-900 border-0 shadow-2xl">
                  <CardHeader>
                    <CardTitle className="text-xl font-bold text-white flex items-center gap-2">
                      <Brain className="w-6 h-6" />
                      AI Deep Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-white/10 backdrop-blur p-5 rounded-xl border border-white/20">
                      <p className="text-white leading-relaxed text-base">
                        {prediction.ai_analysis}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="bg-white/10 backdrop-blur border border-white/20 shadow-2xl h-96 flex items-center justify-center">
                <CardContent>
                  <div className="text-center text-white/60">
                    <Brain className="w-20 h-20 mx-auto mb-4 opacity-50" />
                    <p className="text-xl font-semibold">Select teams and click predict to see results</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Predictions;