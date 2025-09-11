import React from 'react';
import { Heart, Users, Crown } from 'lucide-react';

interface RoleSelectionProps {
  onRoleSelect: (role: 'fan' | 'player' | 'coach') => void;
}

const RoleSelection: React.FC<RoleSelectionProps> = ({ onRoleSelect }) => {
  const roles = [
    {
      id: 'fan' as const,
      name: 'Fan',
      icon: Heart,
      color: 'hot-pink',
      description: 'Follow your favorite teams and players, track match statistics, and get personalized insights.'
    },
    {
      id: 'player' as const,
      name: 'Player',
      icon: Users,
      color: 'lime-green',
      description: 'Monitor your performance, analyze gameplay, and get training recommendations.'
    },
    {
      id: 'coach' as const,
      name: 'Coach',
      icon: Crown,
      color: 'vibrant-orange',
      description: 'Access team analytics, player data, and strategic insights to optimize performance.'
    }
  ];

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-6xl">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="font-orbitron text-4xl md:text-5xl font-black bg-gradient-primary bg-clip-text text-transparent mb-4">
            Football Analytics
          </h1>
        </div>

        {/* Role Selection */}
        <div className="text-center mb-12">
          <h2 className="font-orbitron text-2xl md:text-3xl text-neon-cyan mb-4">
            Choose Your Role
          </h2>
          <p className="text-muted-foreground text-lg mb-8">
            Select how you want to experience Football Analytics
          </p>
        </div>

        {/* Role Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {roles.map((role) => {
            const Icon = role.icon;
            return (
              <div
                key={role.id}
                onClick={() => onRoleSelect(role.id)}
                className="group relative bg-card backdrop-blur-md border border-border rounded-3xl p-8 cursor-pointer transition-all duration-500 hover:-translate-y-2 hover:shadow-glass overflow-hidden"
              >
                {/* Shimmer Effect */}
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                
                {/* Icon */}
                <div className="text-center mb-6">
                  <Icon 
                    size={64} 
                    className={`mx-auto text-${role.color} group-hover:animate-glow transition-all duration-300`}
                  />
                </div>
                
                {/* Content */}
                <div className="text-center">
                  <h3 className="font-orbitron text-xl font-bold mb-4 text-foreground">
                    {role.name}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {role.description}
                  </p>
                </div>

                {/* Hover Border Glow */}
                <div className={`absolute inset-0 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 shadow-${role.color === 'hot-pink' ? 'neon-pink' : role.color === 'lime-green' ? 'neon' : 'neon-blue'} pointer-events-none`} />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default RoleSelection;