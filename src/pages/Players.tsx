import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Navigation from '@/components/Navigation';
import { Search, Trophy, Target } from 'lucide-react';

type Player = {
  id: string;
  name: string;
  position: string;
  jersey_number?: number;
  age?: number;
  nationality?: string;
  market_value?: number;
  goals: number;
  assists: number;
  matches_played: number;
  yellow_cards: number;
  red_cards: number;
  teams?: { name: string };
};

const Players = () => {
  const [players, setPlayers] = useState<Player[]>([]);
  const [filteredPlayers, setFilteredPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [positionFilter, setPositionFilter] = useState('all');

  useEffect(() => {
    fetchPlayers();
  }, []);

  useEffect(() => {
    filterPlayers();
  }, [players, searchTerm, positionFilter]);

  const fetchPlayers = async () => {
    try {
      const { data, error } = await supabase
        .from('players')
        .select(`
          *,
          teams (name)
        `)
        .order('name');

      if (error) throw error;
      setPlayers(data || []);
    } catch (error) {
      console.error('Error fetching players:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterPlayers = () => {
    let filtered = players;

    if (searchTerm) {
      filtered = filtered.filter(player =>
        player.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        player.nationality?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (positionFilter !== 'all') {
      filtered = filtered.filter(player => player.position === positionFilter);
    }

    setFilteredPlayers(filtered);
  };

  const positions = [...new Set(players.map(player => player.position))];

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto p-6 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading players...</p>
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
          <h1 className="text-3xl font-bold mb-4">Players Database</h1>
          
          <div className="flex gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                placeholder="Search by name or nationality..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={positionFilter} onValueChange={setPositionFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by position" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Positions</SelectItem>
                {positions.map(position => (
                  <SelectItem key={position} value={position}>
                    {position}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredPlayers.map((player) => (
            <Card key={player.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center justify-between">
                  <span>{player.name}</span>
                  {player.jersey_number && (
                    <Badge variant="outline">#{player.jersey_number}</Badge>
                  )}
                </CardTitle>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Badge variant="secondary">{player.position}</Badge>
                  {player.teams?.name && (
                    <span className="text-xs">{player.teams.name}</span>
                  )}
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-2">
                  {player.age && (
                    <div className="flex justify-between text-sm">
                      <span>Age:</span>
                      <span>{player.age}</span>
                    </div>
                  )}
                  
                  {player.nationality && (
                    <div className="flex justify-between text-sm">
                      <span>Nationality:</span>
                      <span>{player.nationality}</span>
                    </div>
                  )}
                  
                  <div className="flex justify-between text-sm">
                    <span>Matches:</span>
                    <span>{player.matches_played}</span>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-1">
                      <Trophy className="w-3 h-3 text-yellow-500" />
                      <span>Goals:</span>
                    </div>
                    <span className="font-semibold">{player.goals}</span>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-1">
                      <Target className="w-3 h-3 text-blue-500" />
                      <span>Assists:</span>
                    </div>
                    <span className="font-semibold">{player.assists}</span>
                  </div>
                  
                  {player.market_value && (
                    <div className="flex justify-between text-sm">
                      <span>Value:</span>
                      <span className="font-semibold">
                        €{(player.market_value / 1000000).toFixed(1)}M
                      </span>
                    </div>
                  )}
                  
                  <div className="flex gap-2 pt-2">
                    {player.yellow_cards > 0 && (
                      <Badge variant="destructive" className="text-xs">
                        🟨 {player.yellow_cards}
                      </Badge>
                    )}
                    {player.red_cards > 0 && (
                      <Badge variant="destructive" className="text-xs">
                        🟥 {player.red_cards}
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredPlayers.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground text-lg">No players found matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Players;