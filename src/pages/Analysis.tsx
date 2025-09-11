import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Navigation from '@/components/Navigation';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { BarChart as BarChartIcon, PieChart as PieChartIcon, Trophy, Target, Activity } from 'lucide-react';

type Team = {
  id: string;
  name: string;
  league: string;
};

type Player = {
  id: string;
  name: string;
  position: string;
  goals: number;
  assists: number;
  matches_played: number;
  teams?: { name: string };
};

type Match = {
  id: string;
  home_score?: number;
  away_score?: number;
  status: string;
  league: string;
};

const Analysis = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [players, setPlayers] = useState<Player[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLeague, setSelectedLeague] = useState('all');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [teamsData, playersData, matchesData] = await Promise.all([
        supabase.from('teams').select('*'),
        supabase.from('players').select(`
          *,
          teams (name)
        `),
        supabase.from('matches').select('*').eq('status', 'completed')
      ]);

      setTeams(teamsData.data || []);
      setPlayers(playersData.data || []);
      setMatches(matchesData.data || []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const leagues = [...new Set(teams.map(team => team.league))];

  const filteredPlayers = selectedLeague === 'all' 
    ? players 
    : players.filter(player => {
        const team = teams.find(t => t.name === player.teams?.name);
        return team?.league === selectedLeague;
      });

  const filteredMatches = selectedLeague === 'all'
    ? matches
    : matches.filter(match => match.league === selectedLeague);

  // Top scorers data
  const topScorers = filteredPlayers
    .filter(player => player.goals > 0)
    .sort((a, b) => b.goals - a.goals)
    .slice(0, 10)
    .map(player => ({
      name: player.name.split(' ').pop() || player.name, // Last name for brevity
      goals: player.goals,
      team: player.teams?.name || 'Unknown'
    }));

  // Position distribution data
  const positionData = Object.entries(
    filteredPlayers.reduce((acc, player) => {
      acc[player.position] = (acc[player.position] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  ).map(([position, count]) => ({ position, count }));

  // Goals vs Assists scatter data
  const performanceData = filteredPlayers
    .filter(player => player.goals > 0 || player.assists > 0)
    .slice(0, 20)
    .map(player => ({
      name: player.name.split(' ').pop() || player.name,
      goals: player.goals,
      assists: player.assists,
      total: player.goals + player.assists
    }));

  // Match statistics
  const totalGoals = filteredMatches.reduce((sum, match) => 
    sum + (match.home_score || 0) + (match.away_score || 0), 0
  );
  const averageGoalsPerMatch = filteredMatches.length > 0 ? (totalGoals / filteredMatches.length).toFixed(2) : 0;

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1'];

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto p-6 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading analytics...</p>
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
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold mb-2">Football Analytics Dashboard</h1>
              <p className="text-muted-foreground">Comprehensive analysis of player and team performance</p>
            </div>
            
            <Select value={selectedLeague} onValueChange={setSelectedLeague}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select League" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Leagues</SelectItem>
                {leagues.map(league => (
                  <SelectItem key={league} value={league}>
                    {league}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Key Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Trophy className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Players</p>
                  <p className="text-2xl font-bold">{filteredPlayers.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Target className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Goals</p>
                  <p className="text-2xl font-bold">{totalGoals}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Activity className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Matches Played</p>
                  <p className="text-2xl font-bold">{filteredMatches.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <BarChartIcon className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Avg Goals/Match</p>
                  <p className="text-2xl font-bold">{averageGoalsPerMatch}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Top Scorers Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChartIcon className="w-5 h-5" />
                Top Scorers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topScorers}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="goals" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Position Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChartIcon className="w-5 h-5" />
                Player Positions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={positionData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                    label={({ position, count }) => `${position}: ${count}`}
                  >
                    {positionData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Goals vs Assists */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5" />
                Player Performance: Goals vs Assists
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="goals" stackId="a" fill="#8884d8" />
                  <Bar dataKey="assists" stackId="a" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Top Performers Table */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Top Performers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h4 className="font-semibold mb-3 text-green-600">🏆 Most Goals</h4>
                {topScorers.slice(0, 5).map((player, index) => (
                  <div key={player.name} className="flex justify-between items-center py-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="w-6 h-6 rounded-full p-0 flex items-center justify-center text-xs">
                        {index + 1}
                      </Badge>
                      <span className="text-sm font-medium">{player.name}</span>
                    </div>
                    <Badge variant="secondary">{player.goals}</Badge>
                  </div>
                ))}
              </div>
              
              <div>
                <h4 className="font-semibold mb-3 text-blue-600">🎯 Most Assists</h4>
                {filteredPlayers
                  .filter(player => player.assists > 0)
                  .sort((a, b) => b.assists - a.assists)
                  .slice(0, 5)
                  .map((player, index) => (
                    <div key={player.name} className="flex justify-between items-center py-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="w-6 h-6 rounded-full p-0 flex items-center justify-center text-xs">
                          {index + 1}
                        </Badge>
                        <span className="text-sm font-medium">{player.name.split(' ').pop()}</span>
                      </div>
                      <Badge variant="secondary">{player.assists}</Badge>
                    </div>
                  ))}
              </div>
              
              <div>
                <h4 className="font-semibold mb-3 text-purple-600">⚡ Most Active</h4>
                {filteredPlayers
                  .filter(player => player.matches_played > 0)
                  .sort((a, b) => b.matches_played - a.matches_played)
                  .slice(0, 5)
                  .map((player, index) => (
                    <div key={player.name} className="flex justify-between items-center py-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="w-6 h-6 rounded-full p-0 flex items-center justify-center text-xs">
                          {index + 1}
                        </Badge>
                        <span className="text-sm font-medium">{player.name.split(' ').pop()}</span>
                      </div>
                      <Badge variant="secondary">{player.matches_played}</Badge>
                    </div>
                  ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Analysis;