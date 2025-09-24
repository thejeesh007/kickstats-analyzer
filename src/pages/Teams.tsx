import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Navigation from '@/components/Navigation';
import { Search, Users, Calendar, Trophy } from 'lucide-react';

type Team = {
  id: string;
  name: string;
  league: string;
  founded?: number;
  stadium?: string;
  coach?: string;
  logo_url?: string;
  player_count?: number;
};

const Teams = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [filteredTeams, setFilteredTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [leagueFilter, setLeagueFilter] = useState('all');

  useEffect(() => {
    fetchTeams();
  }, []);

  useEffect(() => {
    filterTeams();
  }, [teams, searchTerm, leagueFilter]);

  const fetchTeams = async () => {
    try {
      const { data: teamsData, error: teamsError } = await supabase
        .from('teams')
        .select('*')
        .order('name');

      if (teamsError) throw teamsError;

      // Get player counts for each team
      const teamsWithCounts = await Promise.all(
        (teamsData || []).map(async (team) => {
          const { count } = await supabase
            .from('players')
            .select('*', { count: 'exact', head: true })
            .eq('team_id', team.id);
          
          return { ...team, player_count: count || 0 };
        })
      );

      setTeams(teamsWithCounts);
    } catch (error) {
      console.error('Error fetching teams:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterTeams = () => {
    let filtered = teams;

    if (searchTerm) {
      filtered = filtered.filter(team =>
        team.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        team.league.toLowerCase().includes(searchTerm.toLowerCase()) ||
        team.coach?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (leagueFilter !== 'all') {
      filtered = filtered.filter(team => team.league === leagueFilter);
    }

    setFilteredTeams(filtered);
  };

  const leagues = [...new Set(teams.map(team => team.league))];

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto p-6 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading teams...</p>
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
          <h1 className="text-3xl font-bold mb-4">Teams Database</h1>
          
          <div className="flex gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                placeholder="Search by team name, league, or coach..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={leagueFilter} onValueChange={setLeagueFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by league" />
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

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTeams.map((team) => (
            <Card key={team.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl flex items-center justify-between">
                  <span>{team.name}</span>
                  <Badge variant="outline">{team.league}</Badge>
                </CardTitle>
              </CardHeader>
              
              <CardContent className="space-y-3">
                {team.coach && (
                  <div className="flex items-center gap-2 text-sm">
                    <Trophy className="w-4 h-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Coach:</span>
                    <span className="font-medium">{team.coach}</span>
                  </div>
                )}
                
                {team.stadium && (
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-4 h-4 text-muted-foreground">🏟️</div>
                    <span className="text-muted-foreground">Stadium:</span>
                    <span>{team.stadium}</span>
                  </div>
                )}
                
                {team.founded && (
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Founded:</span>
                    <span>{team.founded}</span>
                  </div>
                )}
                
                <div className="flex items-center gap-2 text-sm">
                  <Users className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Players:</span>
                  <Badge variant="secondary">{team.player_count}</Badge>
                </div>
                
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground">
                    League: {team.league}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredTeams.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground text-lg">No teams found.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Teams;