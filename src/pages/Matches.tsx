import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Navigation from '@/components/Navigation';
import { Search, Calendar, Clock, Trophy } from 'lucide-react';
import { format } from 'date-fns';

type Match = {
  id: string;
  match_date: string;
  home_score?: number;
  away_score?: number;
  status: string;
  league: string;
  season: string;
  home_team?: { name: string };
  away_team?: { name: string };
};

const Matches = () => {
  const [matches, setMatches] = useState<Match[]>([]);
  const [filteredMatches, setFilteredMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [leagueFilter, setLeagueFilter] = useState('all');

  useEffect(() => {
    fetchMatches();
  }, []);

  useEffect(() => {
    filterMatches();
  }, [matches, searchTerm, statusFilter, leagueFilter]);

  const fetchMatches = async () => {
    try {
      const { data, error } = await supabase
        .from('matches')
        .select(`
          *,
          home_team:teams!matches_home_team_id_fkey (name),
          away_team:teams!matches_away_team_id_fkey (name)
        `)
        .order('match_date', { ascending: false });

      if (error) throw error;
      setMatches(data || []);
    } catch (error) {
      console.error('Error fetching matches:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterMatches = () => {
    let filtered = matches;

    if (searchTerm) {
      filtered = filtered.filter(match =>
        match.home_team?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        match.away_team?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        match.league.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter(match => match.status === statusFilter);
    }

    if (leagueFilter !== 'all') {
      filtered = filtered.filter(match => match.league === leagueFilter);
    }

    setFilteredMatches(filtered);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'default';
      case 'live': return 'destructive';
      case 'scheduled': return 'secondary';
      case 'postponed': return 'outline';
      default: return 'secondary';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'live': return '🔴';
      case 'scheduled': return '⏰';
      case 'postponed': return '⏸️';
      default: return '⏰';
    }
  };

  const statuses = [...new Set(matches.map(match => match.status))];
  const leagues = [...new Set(matches.map(match => match.league))];

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto p-6 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading matches...</p>
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
          <h1 className="text-3xl font-bold mb-4">Match Fixtures & Results</h1>
          
          <div className="flex flex-wrap gap-4 mb-6">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                placeholder="Search by team name or league..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                {statuses.map(status => (
                  <SelectItem key={status} value={status}>
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={leagueFilter} onValueChange={setLeagueFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="League" />
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
          {filteredMatches.map((match) => (
            <Card key={match.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center justify-between text-lg">
                  <Badge variant={getStatusColor(match.status)} className="text-xs">
                    {getStatusIcon(match.status)} {match.status.toUpperCase()}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {match.league}
                  </Badge>
                </CardTitle>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="flex items-center justify-between text-lg font-semibold">
                    <div className="flex-1 text-right">
                      {match.home_team?.name || 'TBD'}
                    </div>
                    
                    <div className="mx-4 text-2xl font-bold text-primary">
                      {match.status === 'completed' ? (
                        <span>{match.home_score ?? 0} - {match.away_score ?? 0}</span>
                      ) : (
                        <span className="text-muted-foreground">VS</span>
                      )}
                    </div>
                    
                    <div className="flex-1 text-left">
                      {match.away_team?.name || 'TBD'}
                    </div>
                  </div>
                </div>
                
                <div className="text-center space-y-2 pt-4 border-t">
                  <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="w-4 h-4" />
                    <span>{format(new Date(match.match_date), 'MMM dd, yyyy')}</span>
                  </div>
                  
                  <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    <span>{format(new Date(match.match_date), 'HH:mm')}</span>
                  </div>
                  
                  <div className="flex items-center justify-center gap-2 text-sm">
                    <Trophy className="w-4 h-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Season {match.season}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredMatches.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground text-lg">No matches found matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Matches;