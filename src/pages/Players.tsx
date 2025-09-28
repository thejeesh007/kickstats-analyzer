"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';

// TypeScript interfaces for API-Football response
interface PlayerStatistics {
  team: {
    id: number;
    name: string;
    logo: string;
  };
  league: {
    id: number;
    name: string;
    country: string;
    logo: string;
    flag: string;
    season: number;
  };
  games: {
    appearences: number;
    lineups: number;
    minutes: number;
    number: number | null;
    position: string;
    rating: string | null;
    captain: boolean;
  };
  substitutes: {
    in: number;
    out: number;
    bench: number;
  };
  shots: {
    total: number | null;
    on: number | null;
  };
  goals: {
    total: number | null;
    conceded: number | null;
    assists: number | null;
    saves: number | null;
  };
  passes: {
    total: number | null;
    key: number | null;
    accuracy: number | null;
  };
  tackles: {
    total: number | null;
    blocks: number | null;
    interceptions: number | null;
  };
  duels: {
    total: number | null;
    won: number | null;
  };
  dribbles: {
    attempts: number | null;
    success: number | null;
    past: number | null;
  };
  fouls: {
    drawn: number | null;
    committed: number | null;
  };
  cards: {
    yellow: number | null;
    yellowred: number | null;
    red: number | null;
  };
  penalty: {
    won: number | null;
    commited: number | null;
    scored: number | null;
    missed: number | null;
    saved: number | null;
  };
}

interface Player {
  id: number;
  name: string;
  firstname: string;
  lastname: string;
  age: number;
  birth: {
    date: string;
    place: string;
    country: string;
  };
  nationality: string;
  height: string | null;
  weight: string | null;
  injured: boolean;
  photo: string;
  statistics: PlayerStatistics[];
}

interface ApiResponse {
  get: string;
  parameters: {
    search: string;
    season: string;
  };
  errors: any[];
  results: number;
  paging: {
    current: number;
    total: number;
  };
  response: {
    player: Player;
    statistics: PlayerStatistics[];
  }[];
}

// Player position options for filtering
const POSITION_OPTIONS = [
  { value: '', label: 'All Positions' },
  { value: 'Goalkeeper', label: 'Goalkeeper' },
  { value: 'Defender', label: 'Defender' },
  { value: 'Midfielder', label: 'Midfielder' },
  { value: 'Attacker', label: 'Forward' },
];

const Players: React.FC = () => {
  // State management
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [positionFilter, setPositionFilter] = useState<string>('');
  const [hasSearched, setHasSearched] = useState<boolean>(false);

  // API configuration
  const API_KEY = process.env.NEXT_PUBLIC_RAPIDAPI_KEY || 'YOUR_API_KEY_HERE';
  const API_HOST = 'api-football-v1.p.rapidapi.com';

  // Fetch players from API-Football
  const fetchPlayers = async (playerName: string) => {
    if (!playerName.trim()) {
      setError('Please enter a player name to search');
      return;
    }

    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await axios.get<ApiResponse>(
        'https://api-football-v1.p.rapidapi.com/v3/players',
        {
          params: {
            search: playerName.trim(),
            season: '2023'
          },
          headers: {
            'X-RapidAPI-Key': API_KEY,
            'X-RapidAPI-Host': API_HOST
          }
        }
      );

      if (response.data.errors && response.data.errors.length > 0) {
        throw new Error(response.data.errors[0]);
      }

      // Transform the response data
      const transformedPlayers: Player[] = response.data.response.map((item) => ({
        ...item.player,
        statistics: item.statistics
      }));

      setPlayers(transformedPlayers);
    } catch (err) {
      console.error('Error fetching players:', err);
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 429) {
          setError('API rate limit exceeded. Please try again later.');
        } else if (err.response?.status === 401) {
          setError('Invalid API key. Please check your configuration.');
        } else {
          setError(err.response?.data?.message || 'Failed to fetch players');
        }
      } else {
        setError('An unexpected error occurred');
      }
      setPlayers([]);
    } finally {
      setLoading(false);
    }
  };

  // Handle search form submission
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPlayers(searchTerm);
  };

  // Handle Enter key press in search input
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch(e as any);
    }
  };

  // Filter players by position
  const filteredPlayers = players.filter((player) => {
    if (!positionFilter) return true;
    
    // Check if player has statistics and matches the position
    return player.statistics.some((stat) => 
      stat.games.position.toLowerCase().includes(positionFilter.toLowerCase())
    );
  });

  // Get player's primary team and position
  const getPrimaryTeamAndPosition = (player: Player) => {
    if (!player.statistics || player.statistics.length === 0) {
      return { teamName: 'Unknown', position: 'Unknown', appearances: 0, goals: 0, assists: 0 };
    }

    // Get the statistics with the most appearances
    const primaryStat = player.statistics.reduce((prev, current) => 
      (prev.games.appearences || 0) > (current.games.appearences || 0) ? prev : current
    );

    return {
      teamName: primaryStat.team.name,
      position: primaryStat.games.position,
      appearances: primaryStat.games.appearences || 0,
      goals: primaryStat.goals.total || 0,
      assists: primaryStat.goals.assists || 0,
      teamLogo: primaryStat.team.logo
    };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            ⚽ Football Player Search
          </h1>
          <p className="text-lg text-gray-600">
            Search for professional football players and their statistics
          </p>
        </div>

        {/* Search Form */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search Input */}
              <div className="flex-1">
                <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
                  Player Name
                </label>
                <input
                  id="search"
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Enter player name (e.g., Messi, Ronaldo, Haaland)"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                  disabled={loading}
                />
              </div>

              {/* Position Filter */}
              <div className="md:w-48">
                <label htmlFor="position" className="block text-sm font-medium text-gray-700 mb-2">
                  Position Filter
                </label>
                <select
                  id="position"
                  value={positionFilter}
                  onChange={(e) => setPositionFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                  disabled={loading}
                >
                  {POSITION_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Search Button */}
              <div className="md:w-32 flex items-end">
                <button
                  type="submit"
                  disabled={loading || !searchTerm.trim()}
                  className="w-full px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    </div>
                  ) : (
                    'Search'
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-flex items-center space-x-2">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="text-lg text-gray-600">Searching for players...</span>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* No Results State */}
        {hasSearched && !loading && !error && filteredPlayers.length === 0 && (
          <div className="text-center py-12">
            <div className="mx-auto h-24 w-24 text-gray-400 mb-4">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No players found</h3>
            <p className="text-gray-600">
              Try adjusting your search term or removing the position filter
            </p>
          </div>
        )}

        {/* Results Count */}
        {filteredPlayers.length > 0 && (
          <div className="mb-6">
            <p className="text-gray-600">
              Found {filteredPlayers.length} player{filteredPlayers.length !== 1 ? 's' : ''}
              {positionFilter && ` (filtered by ${positionFilter})`}
            </p>
          </div>
        )}

        {/* Player Cards Grid */}
        {filteredPlayers.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredPlayers.map((player) => {
              const { teamName, position, appearances, goals, assists, teamLogo } = getPrimaryTeamAndPosition(player);

              return (
                <div
                  key={player.id}
                  className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 overflow-hidden"
                >
                  {/* Player Photo */}
                  <div className="relative h-48 bg-gradient-to-br from-blue-400 to-purple-500">
                    {player.photo ? (
                      <img
                        src={player.photo}
                        alt={player.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <div className="text-white text-6xl font-bold">
                          {player.name.charAt(0)}
                        </div>
                      </div>
                    )}
                    
                    {/* Team Logo Overlay */}
                    {teamLogo && (
                      <div className="absolute top-2 right-2 bg-white rounded-full p-1">
                        <img
                          src={teamLogo}
                          alt={teamName}
                          className="w-8 h-8 object-contain"
                        />
                      </div>
                    )}
                  </div>

                  {/* Player Info */}
                  <div className="p-6">
                    {/* Name */}
                    <h3 className="text-xl font-bold text-gray-900 mb-2 truncate">
                      {player.name}
                    </h3>

                    {/* Basic Info */}
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center text-sm text-gray-600">
                        <span className="font-medium w-20">Age:</span>
                        <span>{player.age} years</span>
                      </div>
                      
                      <div className="flex items-center text-sm text-gray-600">
                        <span className="font-medium w-20">Nation:</span>
                        <span>{player.nationality}</span>
                      </div>

                      <div className="flex items-center text-sm text-gray-600">
                        <span className="font-medium w-20">Team:</span>
                        <span className="truncate">{teamName}</span>
                      </div>

                      <div className="flex items-center text-sm text-gray-600">
                        <span className="font-medium w-20">Position:</span>
                        <span>{position}</span>
                      </div>
                    </div>

                    {/* Statistics */}
                    <div className="border-t pt-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">2023 Season Stats</h4>
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-gray-50 rounded-lg p-2">
                          <div className="text-lg font-bold text-blue-600">{appearances}</div>
                          <div className="text-xs text-gray-500">Matches</div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-2">
                          <div className="text-lg font-bold text-green-600">{goals}</div>
                          <div className="text-xs text-gray-500">Goals</div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-2">
                          <div className="text-lg font-bold text-purple-600">{assists}</div>
                          <div className="text-xs text-gray-500">Assists</div>
                        </div>
                      </div>
                    </div>

                    {/* Injury Status */}
                    {player.injured && (
                      <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-2">
                        <span className="text-red-600 text-sm font-medium">⚠️ Currently Injured</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Players;