import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Calendar, MapPin, Trophy, Clock } from "lucide-react";

interface Fixture {
  fixture: {
    id: number;
    date: string;
    status: { short: string };
  };
  league: {
    id: number;
    name: string;
    logo: string;
  };
  teams: {
    home: { id: number; name: string; logo: string };
    away: { id: number; name: string; logo: string };
  };
  goals: {
    home: number | null;
    away: number | null;
  };
}

export default function Matches() {
  const [country, setCountry] = useState("");
  const [league, setLeague] = useState("");
  const [leagues, setLeagues] = useState<any[]>([]);
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [loading, setLoading] = useState(false);

  const countries = [
    { name: "England", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", color: "from-red-500 to-blue-500" },
    { name: "Spain", flag: "🇪🇸", color: "from-yellow-500 to-red-500" },
    { name: "Germany", flag: "🇩🇪", color: "from-black to-red-500" },
    { name: "Italy", flag: "🇮🇹", color: "from-green-500 to-red-500" }
  ];

  // Fetch leagues based on selected country
  useEffect(() => {
    if (country) {
         fetch(`http://localhost:8000/leagues?country=${country}`)
        .then((res) => res.json())
        .then((data) => setLeagues(data.response || []))
        .catch((err) => console.error("Error fetching leagues:", err));
    }
  }, [country]);

  // Fetch fixtures based on selected league
  useEffect(() => {
    if (league) {
      setLoading(true);
      fetch(`http://localhost:8000/fixtures?league=${league}&season=2020`)
        .then((res) => res.json())
        .then((data) => {
          setFixtures(data.response || []);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Error fetching fixtures:", err);
          setLoading(false);
        });
    }
  }, [league]);

  const getStatusColor = (status: string) => {
    const colors: { [key: string]: string } = {
      FT: "bg-green-500/20 text-green-400 border-green-500/30",
      LIVE: "bg-red-500/20 text-red-400 border-red-500/30 animate-pulse",
      NS: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      PST: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
    };
    return colors[status] || "bg-gray-500/20 text-gray-400 border-gray-500/30";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 relative overflow-hidden">
      {/* Playful Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-10 left-10 w-64 h-64 bg-gradient-to-br from-yellow-300/30 to-orange-300/30 rounded-full blur-3xl animate-blob"></div>
        <div className="absolute top-40 right-20 w-72 h-72 bg-gradient-to-br from-purple-300/30 to-pink-300/30 rounded-full blur-3xl animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-20 left-1/2 w-80 h-80 bg-gradient-to-br from-blue-300/30 to-cyan-300/30 rounded-full blur-3xl animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10 p-6 max-w-7xl mx-auto">
        {/* Playful Header */}
        <div className="text-center mb-10">
          <div className="inline-block animate-bounce-slow mb-4">
            <div className="text-7xl mb-2">⚽</div>
          </div>
          <h1 className="text-5xl font-black mb-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-500 bg-clip-text text-transparent">
            Match Center
          </h1>
          <p className="text-gray-600 text-lg font-medium">Watch the beautiful game unfold! 🎉</p>
        </div>

        {/* Country Selection with Playful Cards */}
        <div className="mb-8">
          <label className="block text-sm font-bold text-gray-700 mb-3 flex items-center justify-center gap-2">
            <MapPin className="w-4 h-4" />
            Choose Your Country
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {countries.map((c) => (
              <button
                key={c.name}
                onClick={() => {
                  setCountry(c.name);
                  setLeague("");
                  setFixtures([]);
                }}
                className={`group relative overflow-hidden rounded-2xl p-6 transition-all duration-300 transform hover:scale-105 ${
                  country === c.name
                    ? "ring-4 ring-purple-500 shadow-2xl"
                    : "hover:shadow-xl"
                }`}
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${c.color} opacity-20 group-hover:opacity-30 transition-opacity`}></div>
                <div className="relative">
                  <div className="text-5xl mb-2 group-hover:scale-110 transition-transform">{c.flag}</div>
                  <p className="font-bold text-gray-800">{c.name}</p>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* League Selection */}
        {country && leagues.length > 0 && (
          <div className="max-w-2xl mx-auto mb-10">
            <label className="block text-sm font-bold text-gray-700 mb-3 flex items-center justify-center gap-2">
              <Trophy className="w-4 h-4" />
              Select League
            </label>
            <Select onValueChange={(val) => setLeague(val)}>
              <SelectTrigger className="w-full bg-white/80 backdrop-blur-sm border-2 border-purple-200 hover:border-purple-400 shadow-lg rounded-2xl h-14 text-lg font-semibold transition-all">
                <SelectValue placeholder="🏆 Choose a league..." />
              </SelectTrigger>
              <SelectContent className="rounded-xl bg-white/95 backdrop-blur-sm">
                {leagues.map((l) => (
                  <SelectItem 
                    key={l.league.id} 
                    value={l.league.id.toString()}
                    className="text-base py-3 cursor-pointer hover:bg-purple-50"
                  >
                    <div className="flex items-center gap-3">
                      <img src={l.league.logo} alt="" className="w-6 h-6" />
                      {l.league.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="relative">
              <div className="w-20 h-20 border-4 border-purple-200 rounded-full"></div>
              <div className="absolute top-0 left-0 w-20 h-20 border-4 border-purple-600 rounded-full border-t-transparent animate-spin"></div>
            </div>
            <p className="mt-6 text-gray-600 font-semibold text-lg">Loading matches...</p>
          </div>
        )}

        {/* Fixtures Grid with Playful Cards */}
        {!loading && fixtures.length > 0 && (
          <div>
            <div className="text-center mb-6">
              <span className="inline-block bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-2 rounded-full font-bold shadow-lg">
                {fixtures.length} Matches Found 🎯
              </span>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {fixtures.map((match, idx) => (
                <div
                  key={match.fixture.id}
                  className="group"
                  style={{
                    animation: `slideUp 0.5s ease-out ${idx * 0.1}s both`
                  }}
                >
                  <Card className="relative overflow-hidden bg-white/90 backdrop-blur-sm border-2 border-transparent hover:border-purple-300 shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 rounded-3xl">
                    {/* League Header */}
                    <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-4 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <img src={match.league.logo} alt="league" className="w-7 h-7 bg-white rounded-full p-1" />
                        <span className="text-white font-bold text-sm">{match.league.name}</span>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(match.fixture.status.short)}`}>
                        {match.fixture.status.short}
                      </span>
                    </div>

                    <CardContent className="p-6">
                      {/* Date & Time */}
                      <div className="flex items-center justify-center gap-2 mb-6 text-gray-500 text-sm">
                        <Calendar className="w-4 h-4" />
                        <span>{new Date(match.fixture.date).toLocaleDateString()}</span>
                        <Clock className="w-4 h-4 ml-2" />
                        <span>{new Date(match.fixture.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>

                      {/* Teams */}
                      <div className="flex items-center justify-between gap-4">
                        {/* Home Team */}
                        <div className="flex-1 flex flex-col items-center">
                          <div className="relative mb-3 group-hover:scale-110 transition-transform">
                            <div className="absolute -inset-2 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full blur opacity-0 group-hover:opacity-50 transition-opacity"></div>
                            <div className="relative w-16 h-16 bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl flex items-center justify-center shadow-md">
                              <img src={match.teams.home.logo} alt={match.teams.home.name} className="w-12 h-12 object-contain" />
                            </div>
                          </div>
                          <p className="text-sm font-bold text-center text-gray-800 line-clamp-2">{match.teams.home.name}</p>
                        </div>

                        {/* Score or VS */}
                        <div className="flex-shrink-0">
                          {match.goals.home !== null && match.goals.away !== null ? (
                            <div className="bg-gradient-to-br from-purple-500 to-pink-500 text-white rounded-2xl px-6 py-4 shadow-lg">
                              <p className="text-3xl font-black text-center">
                                {match.goals.home} : {match.goals.away}
                              </p>
                            </div>
                          ) : (
                            <div className="bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl px-4 py-4 shadow-md">
                              <p className="text-xl font-black text-gray-400">VS</p>
                            </div>
                          )}
                        </div>

                        {/* Away Team */}
                        <div className="flex-1 flex flex-col items-center">
                          <div className="relative mb-3 group-hover:scale-110 transition-transform">
                            <div className="absolute -inset-2 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-full blur opacity-0 group-hover:opacity-50 transition-opacity"></div>
                            <div className="relative w-16 h-16 bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl flex items-center justify-center shadow-md">
                              <img src={match.teams.away.logo} alt={match.teams.away.name} className="w-12 h-12 object-contain" />
                            </div>
                          </div>
                          <p className="text-sm font-bold text-center text-gray-800 line-clamp-2">{match.teams.away.name}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && fixtures.length === 0 && league && (
          <div className="text-center py-20">
            <div className="inline-block p-10 bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border-2 border-purple-200">
              <div className="text-7xl mb-4 animate-bounce">🤔</div>
              <p className="text-2xl font-bold text-gray-700 mb-2">No matches found</p>
              <p className="text-gray-500">Try selecting a different league!</p>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes blob {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
        }
        @keyframes bounce-slow {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-10px);
          }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        .animate-bounce-slow {
          animation: bounce-slow 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
} 