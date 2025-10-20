import { useEffect, useState } from "react";

const Teams = () => {
  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState("");
  const [leagues, setLeagues] = useState([]);
  const [selectedLeague, setSelectedLeague] = useState("");
  const [teams, setTeams] = useState([]);
  const [players, setPlayers] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingPlayers, setLoadingPlayers] = useState(false);

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
      setPlayers([]);
      setSelectedTeam(null);
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

  // Fetch players when clicking a team
  const fetchPlayers = async (teamId) => {
    setLoadingPlayers(true);
    setPlayers([]);
    setSelectedTeam(teamId);
    try {
      const response = await fetch(`http://localhost:8000/players?team=${teamId}&season=2023`);
      const data = await response.json();
      setPlayers(data.response || []);
    } catch (err) {
      console.error("Error fetching players:", err);
    } finally {
      setLoadingPlayers(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-700"></div>
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-pink-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12 space-y-4">
          <div className="inline-block relative">
            <h1 className="text-6xl font-black bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-2 drop-shadow-2xl">
              ⚽ Football Teams
            </h1>
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-lg blur opacity-20"></div>
          </div>
          <p className="text-gray-300 text-lg max-w-2xl mx-auto">
            Explore leagues, teams, and player rosters from around the world
          </p>
        </div>

        {/* Country & League Selectors */}
        <div className="max-w-5xl mx-auto mb-12">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Country Selector */}
            <div className="group relative">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-300"></div>
              <div className="relative bg-slate-800/90 rounded-2xl p-6 border border-slate-700/50">
                <label className="block text-sm font-semibold text-gray-300 mb-3 uppercase">
                  🌍 Select Country
                </label>
                <select
                  value={selectedCountry}
                  onChange={(e) => {
                    setSelectedCountry(e.target.value);
                    setSelectedLeague("");
                    setTeams([]);
                    setPlayers([]);
                    setSelectedTeam(null);
                  }}
                  className="w-full bg-slate-900/50 border border-slate-600 text-white rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">-- Choose Country --</option>
                  {countries.map((c) => (
                    <option key={c.name} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* League Selector */}
            <div className={`group relative ${leagues.length > 0 ? 'opacity-100' : 'opacity-50 pointer-events-none'}`}>
              <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-300"></div>
              <div className="relative bg-slate-800/90 rounded-2xl p-6 border border-slate-700/50">
                <label className="block text-sm font-semibold text-gray-300 mb-3 uppercase">
                  🏆 Select League
                </label>
                <select
                  value={selectedLeague}
                  onChange={(e) => setSelectedLeague(e.target.value)}
                  className="w-full bg-slate-900/50 border border-slate-600 text-white rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-pink-500"
                >
                  <option value="">-- Choose League --</option>
                  {leagues.map((l) => (
                    <option key={l.league.id} value={l.league.id}>
                      {l.league.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Teams Display */}
        {loading ? (
          <div className="text-center text-gray-300 py-20">Loading teams...</div>
        ) : teams.length > 0 ? (
          <div>
            <div className="mb-6 text-center">
              <span className="inline-block bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-purple-500/30 rounded-full px-6 py-2 text-sm text-purple-300 font-semibold">
                {teams.length} Teams Found
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
              {teams.map((t, idx) => {
                const team = t.team;
                return (
                  <div
                    key={team.id}
                    onClick={() => fetchPlayers(team.id)}
                    className={`group relative cursor-pointer ${
                      selectedTeam === team.id ? "ring-2 ring-purple-500" : ""
                    }`}
                    style={{ animation: `fadeIn 0.5s ease-out ${idx * 0.05}s both` }}
                  >
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-2xl blur opacity-0 group-hover:opacity-75 transition duration-500"></div>
                    <div className="relative bg-slate-800/80 rounded-2xl p-6 border border-slate-700/50 hover:border-purple-500 transition-all duration-300 text-center">
                      <img src={team.logo} alt={team.name} className="w-16 h-16 mx-auto mb-3 object-contain" />
                      <h3 className="text-lg font-bold text-white">{team.name}</h3>
                      <p className="text-sm text-gray-400">{team.country}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : selectedLeague ? (
          <div className="text-center text-gray-300 py-20">No teams found for this league.</div>
        ) : null}

        {/* Players Display */}
        {loadingPlayers ? (
          <div className="text-center text-gray-300 py-10">Loading players...</div>
        ) : players.length > 0 ? (
          <div className="mt-12">
            <h2 className="text-3xl font-bold text-center text-white mb-8">
              👥 Players of {players[0]?.team?.name || "Team"}
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
              {players.map((p) => (
                <div key={p.player.id} className="bg-slate-800/80 rounded-xl p-4 text-center border border-slate-700/50 hover:border-purple-500 transition">
                  <img
                    src={p.player.photo}
                    alt={p.player.name}
                    className="w-20 h-20 mx-auto rounded-full mb-3 object-cover"
                  />
                  <h4 className="text-white font-semibold text-sm">{p.player.name}</h4>
                  <p className="text-gray-400 text-xs">
                    {p.statistics[0]?.games?.position || "—"} | {p.player.nationality}
                  </p>
                </div>
              ))}
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
