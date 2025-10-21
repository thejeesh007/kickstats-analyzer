import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Calendar, MapPin, Trophy, Clock } from "lucide-react";

interface Fixture {
  fixture: { id: number; date: string; status: { short: string } };
  league: { id: number; name: string; logo: string };
  teams: {
    home: { id: number; name: string; logo: string };
    away: { id: number; name: string; logo: string };
  };
  goals: { home: number | null; away: number | null };
}

export default function Matches() {
  const [countries, setCountries] = useState<any[]>([]);
  const [country, setCountry] = useState("");
  const [leagues, setLeagues] = useState<any[]>([]);
  const [league, setLeague] = useState("");
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch countries dynamically
  useEffect(() => {
    fetch("http://localhost:8000/countries")
      .then((res) => res.json())
      .then((data) => setCountries(data.response || []))
      .catch((err) => console.error("Error fetching countries:", err));
  }, []);

  // Fetch leagues for selected country
  useEffect(() => {
    if (country) {
      setLeagues([]);
      setFixtures([]);
         fetch(`http://localhost:8000/leagues?country=${country}`)
        .then((res) => res.json())
        .then((data) => setLeagues(data.response || []))
        .catch((err) => console.error("Error fetching leagues:", err));
    }
  }, [country]);

  // Fetch fixtures for selected league
  useEffect(() => {
    if (league) {
      setLoading(true);
      fetch(`http://localhost:8000/fixtures?league=${league}&season=2023`)
        .then((res) => res.json())
        .then((data) => {
          setFixtures(data.fixtures || []);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Error fetching fixtures:", err);
          setLoading(false);
        });
    }
  }, [league]);

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      FT: "bg-green-500/20 text-green-500 border-green-500/30",
      LIVE: "bg-red-500/20 text-red-500 border-red-500/30 animate-pulse",
      NS: "bg-blue-500/20 text-blue-500 border-blue-500/30",
      PST: "bg-yellow-500/20 text-yellow-500 border-yellow-500/30"
    };
    return colors[status] || "bg-gray-500/20 text-gray-400 border-gray-500/30";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-200 via-yellow-200 to-cyan-200 relative overflow-hidden">
      {/* Decorative background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-10 left-10 w-64 h-64 bg-gradient-to-br from-rose-400/40 to-orange-400/40 rounded-full blur-3xl animate-blob"></div>
        <div className="absolute top-40 right-20 w-72 h-72 bg-gradient-to-br from-violet-400/40 to-fuchsia-400/40 rounded-full blur-3xl animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-20 left-1/2 w-80 h-80 bg-gradient-to-br from-emerald-400/40 to-teal-400/40 rounded-full blur-3xl animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10 p-6 max-w-6xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-6xl font-black mb-3 bg-gradient-to-r from-rose-500 via-purple-500 via-blue-500 to-teal-500 bg-clip-text text-transparent drop-shadow-lg">
            Match Center ⚽
          </h1>
          <p className="text-gray-700 text-xl font-bold">Explore real upcoming matches from around the world 🌍✨</p>
        </div>

        {/* Country Dropdown */}
        <div className="max-w-md mx-auto mb-6">
          <label className="block text-sm font-bold text-gray-800 mb-2 flex items-center gap-2 justify-center">
            <MapPin className="w-5 h-5 text-rose-500" /> Select a Country
          </label>
          <Select onValueChange={(val) => setCountry(val)}>
            <SelectTrigger className="w-full bg-gradient-to-r from-rose-100 to-orange-100 backdrop-blur-sm border-3 border-rose-400 hover:border-orange-500 shadow-xl rounded-2xl h-16 text-lg font-bold transition-all hover:scale-105">
              <SelectValue placeholder="🌎 Choose a country..." />
            </SelectTrigger>
            <SelectContent className="rounded-xl bg-white/95 backdrop-blur-sm max-h-64 overflow-y-auto border-2 border-rose-300">
              {countries.map((c) => (
                <SelectItem key={c.name} value={c.name} className="text-base py-2 cursor-pointer hover:bg-gradient-to-r hover:from-rose-100 hover:to-orange-100">
                  <div className="flex items-center gap-3">
                    <img src={c.flag} alt={c.name} className="w-6 h-4 rounded-sm border" />
                    {c.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* League Dropdown */}
        {country && leagues.length > 0 && (
          <div className="max-w-md mx-auto mb-10">
            <label className="block text-sm font-bold text-gray-800 mb-2 flex items-center gap-2 justify-center">
              <Trophy className="w-5 h-5 text-yellow-500" /> Select a League
            </label>
            <Select onValueChange={(val) => setLeague(val)}>
              <SelectTrigger className="w-full bg-gradient-to-r from-yellow-100 to-amber-100 backdrop-blur-sm border-3 border-yellow-400 hover:border-amber-500 shadow-xl rounded-2xl h-16 text-lg font-bold transition-all hover:scale-105">
                <SelectValue placeholder="🏆 Choose a league..." />
              </SelectTrigger>
              <SelectContent className="rounded-xl bg-white/95 backdrop-blur-sm max-h-64 overflow-y-auto border-2 border-yellow-300">
                {leagues.map((l) => (
                  <SelectItem key={l.league.id} value={l.league.id.toString()} className="text-base py-3 hover:bg-gradient-to-r hover:from-yellow-100 hover:to-amber-100">
                    <div className="flex items-center gap-3">
                      <img src={l.league.logo} alt={l.league.name} className="w-6 h-6" />
                      {l.league.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Fixtures Display */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-12 h-12 animate-spin text-rose-500" />
            <p className="mt-4 text-gray-700 font-bold text-lg">Fetching upcoming matches... 🔄</p>
          </div>
        )}

        {!loading && fixtures.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {fixtures.map((match) => (
              <Card key={match.fixture.id} className="relative overflow-hidden bg-white/95 backdrop-blur-sm border-4 border-transparent hover:border-gradient-to-r hover:from-pink-400 hover:to-purple-400 shadow-2xl hover:shadow-pink-300/50 transition-all duration-300 transform hover:-translate-y-3 hover:rotate-1 rounded-3xl">
                <div className="bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 p-4 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <img src={match.league.logo} alt="league" className="w-7 h-7 bg-white rounded-full p-1 shadow-lg" />
                    <span className="text-white font-black text-sm drop-shadow-lg">{match.league.name}</span>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold border-2 shadow-lg ${getStatusColor(match.fixture.status.short)}`}>
                    {match.fixture.status.short}
                  </span>
                </div>
                <CardContent className="p-6 text-center bg-gradient-to-br from-white to-gray-50">
                  <div className="text-gray-600 text-sm font-semibold mb-4 flex justify-center items-center gap-3">
                    <Calendar className="w-4 h-4 text-blue-500" />
                    {new Date(match.fixture.date).toLocaleDateString()} •
                    <Clock className="w-4 h-4 text-green-500" />
                    {new Date(match.fixture.date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex flex-col items-center flex-1">
                      <div className="bg-gradient-to-br from-blue-100 to-cyan-100 rounded-2xl p-3 mb-2 shadow-md">
                        <img src={match.teams.home.logo} alt={match.teams.home.name} className="w-12 h-12" />
                      </div>
                      <p className="font-bold text-gray-800">{match.teams.home.name}</p>
                    </div>
                    <p className="font-black text-2xl bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">VS</p>
                    <div className="flex flex-col items-center flex-1">
                      <div className="bg-gradient-to-br from-rose-100 to-pink-100 rounded-2xl p-3 mb-2 shadow-md">
                        <img src={match.teams.away.logo} alt={match.teams.away.name} className="w-12 h-12" />
                      </div>
                      <p className="font-bold text-gray-800">{match.teams.away.name}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}