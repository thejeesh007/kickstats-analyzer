"use client";

import React, { useState } from "react";
import axios from "axios";

// --- Types ---
interface PlayerStatistics {
  team: { id: number; name: string; logo: string };
  league: { id: number; name: string; season: number };
  games: { appearences: number; position: string };
  goals: { total: number | null; assists: number | null };
}

interface Player {
  id: number;
  name: string;
  age: number;
  nationality: string;
  photo: string;
  injured: boolean;
  statistics: PlayerStatistics[];
}

interface ApiResponse {
  response: {
    player: Player;
    statistics: PlayerStatistics[];
  }[];
}

// --- Filters ---
const POSITION_OPTIONS = [
  { value: "", label: "All Positions" },
  { value: "Goalkeeper", label: "Goalkeeper" },
  { value: "Defender", label: "Defender" },
  { value: "Midfielder", label: "Midfielder" },
  { value: "Attacker", label: "Forward" },
];

const Players: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [positionFilter, setPositionFilter] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  // API config
  const API_KEY = process.env.NEXT_PUBLIC_RAPIDAPI_KEY!;
  const API_HOST = "api-football-v1.p.rapidapi.com";

  // --- Fetch Players ---
  const fetchPlayers = async (playerName: string) => {
    if (!playerName.trim()) {
      setError("Please enter a player name");
      return;
    }

    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const { data } = await axios.get<ApiResponse>(
        "https://api-football-v1.p.rapidapi.com/v3/players",
        {
          params: { search: playerName.trim(), season: "2023" },
          headers: {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": API_HOST,
          },
        }
      );

      const transformed = data.response.map((item) => ({
        ...item.player,
        statistics: item.statistics,
      }));

      setPlayers(transformed);
    } catch (err: any) {
      console.error("Error fetching players:", err);
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 429) setError("Rate limit exceeded, try later.");
        else if (err.response?.status === 401) setError("Invalid API key.");
        else setError(err.response?.data?.message || "Failed to fetch players");
      } else {
        setError("Unexpected error");
      }
      setPlayers([]);
    } finally {
      setLoading(false);
    }
  };

  // --- Handlers ---
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPlayers(searchTerm);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch(e as any);
  };

  // --- Helpers ---
  const filteredPlayers = players.filter((p) =>
    positionFilter
      ? p.statistics.some((s) =>
          s.games.position.toLowerCase().includes(positionFilter.toLowerCase())
        )
      : true
  );

  const getPrimaryStats = (player: Player) => {
    if (!player.statistics.length) {
      return { team: "Unknown", pos: "Unknown", apps: 0, goals: 0, assists: 0, logo: "" };
    }

    const best = player.statistics.reduce((prev, cur) =>
      (prev.games.appearences || 0) > (cur.games.appearences || 0) ? prev : cur
    );

    return {
      team: best.team.name,
      pos: best.games.position,
      apps: best.games.appearences || 0,
      goals: best.goals.total || 0,
      assists: best.goals.assists || 0,
      logo: best.team.logo,
    };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold">⚽ Football Player Search</h1>
          <p className="text-gray-600">Search for professional football players</p>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="bg-white shadow-lg rounded-xl p-6 mb-8 flex flex-col md:flex-row gap-4">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter player name (e.g., Messi)"
            className="flex-1 px-4 py-2 border rounded-lg"
          />
          <select
            value={positionFilter}
            onChange={(e) => setPositionFilter(e.target.value)}
            className="px-4 py-2 border rounded-lg md:w-48"
          >
            {POSITION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={loading || !searchTerm.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? "Loading..." : "Search"}
          </button>
        </form>

        {/* Error */}
        {error && <div className="text-red-600 text-center mb-4">{error}</div>}

        {/* Results */}
        {filteredPlayers.length > 0 && (
          <p className="mb-6 text-gray-600">
            Found {filteredPlayers.length} player{filteredPlayers.length > 1 && "s"}
          </p>
        )}

        {/* Player Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPlayers.map((p) => {
            const { team, pos, apps, goals, assists, logo } = getPrimaryStats(p);

            return (
              <div key={p.id} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition">
                {/* Banner */}
                <div className="relative h-48 bg-gradient-to-r from-blue-400 to-purple-500">
                  {p.photo && (
                    <img src={p.photo} alt={p.name} className="w-full h-full object-cover" />
                  )}
                  {logo && (
                    <img src={logo} alt={team} className="absolute top-2 right-2 w-10 h-10 rounded-full bg-white p-1" />
                  )}
                </div>

                {/* Content */}
                <div className="p-6">
                  <h3 className="text-xl font-bold mb-2">{p.name}</h3>
                  <p className="text-sm text-gray-600">Age: {p.age} | {p.nationality}</p>
                  <p className="text-sm text-gray-600">Team: {team} | Position: {pos}</p>

                  <div className="grid grid-cols-3 gap-2 mt-4 text-center">
                    <div className="bg-gray-50 rounded-lg p-2">
                      <div className="font-bold">{apps}</div>
                      <div className="text-xs">Matches</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-2">
                      <div className="font-bold text-green-600">{goals}</div>
                      <div className="text-xs">Goals</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-2">
                      <div className="font-bold text-purple-600">{assists}</div>
                      <div className="text-xs">Assists</div>
                    </div>
                  </div>

                  {p.injured && (
                    <p className="mt-3 text-red-600 font-medium">⚠️ Currently Injured</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* No results */}
        {hasSearched && !loading && !error && filteredPlayers.length === 0 && (
          <p className="text-center text-gray-600 mt-12">No players found</p>
        )}
      </div>
    </div>
  );
};

export default Players;
