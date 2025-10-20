import { useEffect, useState } from "react";

const Teams = () => {
  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState("");
  const [leagues, setLeagues] = useState([]);
  const [selectedLeague, setSelectedLeague] = useState("");
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch countries
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const response = await fetch("http://localhost:8000/countries");
        const data = await response.json();
        setCountries(data.response || []);
      } catch (err) {
        console.error("Error fetching countries:", err);
      }
    };
    fetchCountries();
  }, []);

  // Fetch leagues for a country
  useEffect(() => {
    if (!selectedCountry) return;
    const fetchLeagues = async () => {
      try {
        const response = await fetch(`http://localhost:8000/leagues?country=${selectedCountry}`);
        const data = await response.json();
        setLeagues(data.response || []);
      } catch (err) {
        console.error("Error fetching leagues:", err);
      }
    };
    fetchLeagues();
  }, [selectedCountry]);

  // Fetch teams for a league
  useEffect(() => {
    if (!selectedLeague) return;
    const fetchTeams = async () => {
      setLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/teams/${selectedLeague}?season=2023`);
        const data = await response.json();
        setTeams(data.response || []);
      } catch (err) {
        console.error("Error fetching teams:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchTeams();
  }, [selectedLeague]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-700"></div>
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-pink-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-12">
        {/* Header Section */}
        <div className="text-center mb-12 space-y-4">
          <div className="inline-block">
            <div className="relative">
              <h1 className="text-6xl font-black bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-2 drop-shadow-2xl">
                ⚽ Football Teams
              </h1>
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-lg blur opacity-20"></div>
            </div>
          </div>
          <p className="text-gray-300 text-lg max-w-2xl mx-auto">
            Explore teams from leagues around the world with stunning visuals
          </p>
        </div>

        {/* Selection Cards */}
        <div className="max-w-5xl mx-auto mb-12">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Country Selector Card */}
            <div className="group relative">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-300"></div>
              <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                <label className="block text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wider">
                  🌍 Select Country
                </label>
                <select
                  value={selectedCountry}
                  onChange={(e) => {
                    setSelectedCountry(e.target.value);
                    setSelectedLeague("");
                    setTeams([]);
                  }}
                  className="w-full bg-slate-900/50 border border-slate-600 text-white rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 cursor-pointer hover:border-purple-500"
                >
                  <option value="" className="bg-slate-900">-- Choose Country --</option>
                  {countries.map((c) => (
                    <option key={c.name} value={c.name} className="bg-slate-900">
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* League Selector Card */}
            <div className={`group relative transition-all duration-500 ${leagues.length > 0 ? 'opacity-100' : 'opacity-50 pointer-events-none'}`}>
              <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-300"></div>
              <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                <label className="block text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wider">
                  🏆 Select League
                </label>
                <select
                  value={selectedLeague}
                  onChange={(e) => setSelectedLeague(e.target.value)}
                  disabled={leagues.length === 0}
                  className="w-full bg-slate-900/50 border border-slate-600 text-white rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent transition-all duration-300 cursor-pointer hover:border-pink-500 disabled:cursor-not-allowed"
                >
                  <option value="" className="bg-slate-900">-- Choose League --</option>
                  {leagues.map((l) => (
                    <option key={l.league.id} value={l.league.id} className="bg-slate-900">
                      {l.league.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Teams Grid */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="relative w-24 h-24">
              <div className="absolute inset-0 border-4 border-purple-500/30 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-transparent border-t-purple-500 rounded-full animate-spin"></div>
            </div>
            <p className="text-gray-300 mt-6 text-lg font-medium">Loading teams...</p>
          </div>
        ) : teams.length > 0 ? (
          <div>
            <div className="mb-6 text-center">
              <span className="inline-block bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-purple-500/30 rounded-full px-6 py-2 text-sm text-purple-300 font-semibold">
                {teams.length} Teams Found
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {teams.map((t, idx) => {
                const team = t.team;
                return (
                  <div
                    key={team.id}
                    className="group relative"
                    style={{
                      animation: `fadeIn 0.5s ease-out ${idx * 0.05}s both`
                    }}
                  >
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-2xl blur opacity-0 group-hover:opacity-75 transition duration-500"></div>
                    <div className="relative bg-slate-800/80 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 hover:border-purple-500/50 transition-all duration-300 transform hover:-translate-y-2 hover:shadow-2xl h-full flex flex-col">
                      <div className="flex-shrink-0 mb-4">
                        <div className="w-20 h-20 mx-auto bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-3 shadow-xl group-hover:shadow-purple-500/50 transition-all duration-300 flex items-center justify-center">
                          <img
                            src={team.logo}
                            alt={team.name}
                            className="w-full h-full object-contain group-hover:scale-110 transition-transform duration-300"
                            onError={(e) => {
                              e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23a855f7'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'/%3E%3C/svg%3E";
                            }}
                          />
                        </div>
                      </div>
                      <div className="flex-grow flex flex-col justify-between">
                        <div>
                          <h3 className="text-lg font-bold text-white mb-1 line-clamp-2 group-hover:text-purple-300 transition-colors">
                            {team.name}
                          </h3>
                          <p className="text-sm text-gray-400 mb-2">{team.country}</p>
                        </div>
                        <div className="mt-3 pt-3 border-t border-slate-700/50">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-500">Founded</span>
                            <span className="text-purple-400 font-semibold">
                              {team.founded || "N/A"}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : selectedLeague ? (
          <div className="text-center py-20">
            <div className="inline-block p-8 bg-slate-800/50 backdrop-blur-xl rounded-3xl border border-slate-700/50">
              <div className="text-6xl mb-4">😔</div>
              <p className="text-gray-300 text-lg">No teams found for this league</p>
            </div>
          </div>
        ) : null}
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default Teams;