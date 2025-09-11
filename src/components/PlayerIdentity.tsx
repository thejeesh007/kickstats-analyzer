import React, { useState } from 'react';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { supabase } from '@/integrations/supabase/client';

interface PlayerIdentityProps {
  onBack: () => void;
  onComplete: () => void;
}

const PlayerIdentity: React.FC<PlayerIdentityProps> = ({ onBack, onComplete }) => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    team: '',
    position: '',
    jerseyNumber: ''
  });

  const positions = [
    'Forward',
    'Midfielder',
    'Defender',
    'Goalkeeper'
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    // Validate required fields
    if (!formData.name || !formData.team || !formData.position) {
      setMessage({ type: 'error', text: 'Please fill in all required fields' });
      setLoading(false);
      return;
    }

    try {
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        setMessage({ type: 'error', text: 'Please log in first' });
        setLoading(false);
        return;
      }

      const { error } = await supabase
        .from('profiles')
        .insert({
          id: user.id,
          email: user.email!,
          name: formData.name,
          role: 'player',
          player_team: formData.team,
          player_position: formData.position,
          player_jersey_number: formData.jerseyNumber ? parseInt(formData.jerseyNumber) : null
        });

      if (error) {
        setMessage({ type: 'error', text: error.message });
      } else {
        setMessage({ type: 'success', text: 'Player profile completed successfully!' });
        setTimeout(() => onComplete(), 1000);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save player profile. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="relative bg-card backdrop-blur-md border border-border rounded-3xl p-8 shadow-glass">
          {/* Back Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onBack}
            className="absolute top-4 left-4 text-muted-foreground hover:text-neon-cyan"
          >
            <ArrowLeft size={20} />
          </Button>

          {/* Header */}
          <div className="text-center mb-6 pt-6">
            <h2 className="font-orbitron text-2xl font-bold text-lime-green mb-2">
              Player Profile Setup
            </h2>
            <p className="text-muted-foreground">
              Complete your player profile to get started
            </p>
          </div>

          {/* Message */}
          {message && (
            <Alert className={`mb-6 ${
              message.type === 'error' 
                ? 'border-error-red/40 bg-error-red/10' 
                : 'border-success-green/40 bg-success-green/10'
            }`}>
              <AlertDescription className={
                message.type === 'error' ? 'text-error-red' : 'text-success-green'
              }>
                {message.text}
              </AlertDescription>
            </Alert>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="playerName" className="text-xs uppercase tracking-wider text-muted-foreground">
                Full Name *
              </Label>
              <Input
                id="playerName"
                type="text"
                placeholder="Enter your full name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-lime-green focus:shadow-neon transition-all duration-300"
                required
              />
            </div>

            <div>
              <Label htmlFor="playerTeam" className="text-xs uppercase tracking-wider text-muted-foreground">
                Current Team *
              </Label>
              <Input
                id="playerTeam"
                type="text"
                placeholder="e.g. FC Barcelona U23"
                value={formData.team}
                onChange={(e) => setFormData({ ...formData, team: e.target.value })}
                className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-lime-green focus:shadow-neon transition-all duration-300"
                required
              />
            </div>

            <div>
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">
                Position *
              </Label>
              <Select value={formData.position} onValueChange={(value) => setFormData({ ...formData, position: value })}>
                <SelectTrigger className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-lime-green focus:shadow-neon transition-all duration-300">
                  <SelectValue placeholder="Select your position" />
                </SelectTrigger>
                <SelectContent className="bg-card border-border rounded-xl">
                  {positions.map((position) => (
                    <SelectItem 
                      key={position} 
                      value={position}
                      className="focus:bg-muted/50 focus:text-foreground"
                    >
                      {position}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="jerseyNumber" className="text-xs uppercase tracking-wider text-muted-foreground">
                Jersey Number (Optional)
              </Label>
              <Input
                id="jerseyNumber"
                type="number"
                min="1"
                max="99"
                placeholder="e.g. 10"
                value={formData.jerseyNumber}
                onChange={(e) => setFormData({ ...formData, jerseyNumber: e.target.value })}
                className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-lime-green focus:shadow-neon transition-all duration-300"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-lime-green to-electric-blue hover:from-electric-blue hover:to-lime-green text-white font-orbitron font-bold py-3 rounded-2xl transition-all duration-300 hover:shadow-neon hover:-translate-y-1"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Completing profile...
                </>
              ) : (
                'Complete Profile'
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default PlayerIdentity;