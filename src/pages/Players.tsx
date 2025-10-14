import React, { useState, useEffect } from "react";
import { createClient } from "@supabase/supabase-js";

// --- Supabase setup ---
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

interface Player {
  id: number;
  name: string;
  age: number;
  nationality: string;
  club: string;
  league: string;
}

const Players: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // Fetch players from Supabase
  const fetchPlayers = async (search: string) => {
    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      let query = supabase.from("players").select("*");

      if (search.trim()) {
        query = query.ilike("name", `%${search.trim()}%`);
      }

      const { data, error } = await query;

      if (error) throw error;
      setPlayers(data || []);
    } catch (err: any) {
      console.error("Error fetching players:", err.message);
      setError("Failed to fetch players from Supabase");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPlayers(searchTerm);
  };

  useEffect(() => {
    fetchPlayers("");
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <div className="text-6xl mb-2">⚽</div>
          <h1 className="text-4xl font-extrabold text-white mb-3 tracking-tight">
            Player Database
          </h1>
          <p className="text-blue-200 text-lg">Search for players from your Supabase table</p>
        </div>

        {/* Search bar */}
        <form
          onSubmit={handleSearch}
          className="bg-white/10 backdrop-blur border border-white/20 shadow-xl rounded-2xl p-6 mb-10 flex flex-col md:flex-row gap-4"
        >
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Enter player name (e.g., Messi)"
            className="flex-1 px-5 py-3 bg-white/90 border-2 border-transparent focus:border-blue-400 rounded-xl text-gray-800 placeholder-gray-500 outline-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        {error && (
          <div className="bg-red-500/20 text-red-100 border border-red-400/50 rounded-xl p-4 mb-8 text-center">
            ⚠️ {error}
          </div>
        )}

        {/* Player Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {players.map((p) => (
            <div
              key={p.id}
              className="bg-white/95 backdrop-blur rounded-2xl shadow-xl border border-white/40 p-6 hover:scale-105 transition-all duration-300"
            >
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{p.name}</h3>
              <p className="text-gray-700">
                <span className="font-semibold">Age:</span> {p.age}
              </p>
              <p className="text-gray-700">
                <span className="font-semibold">Nationality:</span> {p.nationality}
              </p>
              <p className="text-gray-700">
                <span className="font-semibold">Club:</span> {p.club}
              </p>
              <p className="text-gray-700">
                <span className="font-semibold">League:</span> {p.league}
              </p>
            </div>
          ))}
        </div>

        {hasSearched && !loading && players.length === 0 && (
          <div className="text-center mt-16 text-blue-200 text-xl">
            🔍 No players found. Try another name.
          </div>
        )}
      </div>
    </div>
  );
};

export default Players;
