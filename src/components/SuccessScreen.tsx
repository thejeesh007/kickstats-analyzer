import React from 'react';
import { CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SuccessScreenProps {
  role: 'fan' | 'player' | 'coach';
  onContinue: () => void;
}

const SuccessScreen: React.FC<SuccessScreenProps> = ({ role, onContinue }) => {
  const roleMessages = {
    fan: {
      title: 'Welcome to Football Analytics!',
      subtitle: 'Your fan account has been created successfully.',
      description: 'You can now follow your favorite teams, track match statistics, and get personalized insights.',
      buttonText: 'Go to Fan Dashboard'
    },
    player: {
      title: 'Player Profile Created!',
      subtitle: 'Your player account is now complete.',
      description: 'Access performance analytics, training recommendations, and track your gameplay statistics.',
      buttonText: 'Go to Player Dashboard'
    },
    coach: {
      title: 'Coach Profile Created!',
      subtitle: 'Your coaching account is ready to use.',
      description: 'Access team analytics, player data, and strategic insights to optimize team performance.',
      buttonText: 'Go to Coach Dashboard'
    }
  };

  const message = roleMessages[role];

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-card backdrop-blur-md border border-border rounded-3xl p-8 shadow-glass text-center">
          {/* Success Icon */}
          <div className="mb-8">
            <div className="mx-auto w-20 h-20 bg-success-green/20 rounded-full flex items-center justify-center animate-glow">
              <CheckCircle size={48} className="text-success-green" />
            </div>
          </div>

          {/* Content */}
          <div className="space-y-4 mb-8">
            <h2 className="font-orbitron text-2xl font-bold text-success-green">
              {message.title}
            </h2>
            <p className="font-semibold text-foreground">
              {message.subtitle}
            </p>
            <p className="text-muted-foreground leading-relaxed">
              {message.description}
            </p>
          </div>

          {/* Continue Button */}
          <Button
            onClick={onContinue}
            className="w-full bg-gradient-to-r from-success-green to-neon-cyan hover:from-neon-cyan hover:to-success-green text-white font-orbitron font-bold py-3 rounded-2xl transition-all duration-300 hover:shadow-neon hover:-translate-y-1"
          >
            {message.buttonText}
          </Button>

          {/* Celebratory Elements */}
          <div className="mt-8 space-y-2 opacity-50">
            <div className="flex justify-center space-x-2">
              <div className="w-2 h-2 bg-neon-cyan rounded-full animate-pulse" />
              <div className="w-2 h-2 bg-electric-blue rounded-full animate-pulse delay-100" />
              <div className="w-2 h-2 bg-hot-pink rounded-full animate-pulse delay-200" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SuccessScreen;