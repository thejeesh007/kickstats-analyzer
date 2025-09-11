import React, { useState } from 'react';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { supabase } from '@/integrations/supabase/client';

interface CoachIdentityProps {
  onBack: () => void;
  onComplete: () => void;
}

const CoachIdentity: React.FC<CoachIdentityProps> = ({ onBack, onComplete }) => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    team: '',
    experience: '',
    license: ''
  });

  const licenses = [
    'UEFA A',
    'UEFA B',
    'UEFA Pro',
    'FA Level 1',
    'FA Level 2',
    'Other'
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    // Validate required fields
    if (!formData.name || !formData.team || !formData.experience || !formData.license) {
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
          role: 'coach',
          coach_team: formData.team,
          coach_experience: parseInt(formData.experience),
          coach_license: formData.license
        });

      if (error) {
        setMessage({ type: 'error', text: error.message });
      } else {
        setMessage({ type: 'success', text: 'Coach profile completed successfully!' });
        setTimeout(() => onComplete(), 1000);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save coach profile. Please try again.' });
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
            <h2 className="font-orbitron text-2xl font-bold text-vibrant-orange mb-2">
              Coach Profile Setup
            </h2>
            <p className="text-muted-foreground">
              Complete your coaching profile to get started
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
              <Label htmlFor="coachName" className="text-xs uppercase tracking-wider text-muted-foreground">
                Full Name *
              </Label>
              <Input
                id="coachName"
                type="text"
                placeholder="Enter your full name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-vibrant-orange focus:shadow-neon transition-all duration-300"
                required
              />
            </div>

            <div>
              <Label htmlFor="coachTeam" className="text-xs uppercase tracking-wider text-muted-foreground">
                Team You Coach *
              </Label>
              <Input
                id="coachTeam"
                type="text"
                placeholder="e.g. Manchester United U18"
                value={formData.team}
                onChange={(e) => setFormData({ ...formData, team: e.target.value })}
                className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-vibrant-orange focus:shadow-neon transition-all duration-300"
                required
              />
            </div>

            <div>
              <Label htmlFor="experience" className="text-xs uppercase tracking-wider text-muted-foreground">
                Years of Experience *
              </Label>
              <Input
                id="experience"
                type="number"
                min="1"
                max="50"
                placeholder="e.g. 8"
                value={formData.experience}
                onChange={(e) => setFormData({ ...formData, experience: e.target.value })}
                className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-vibrant-orange focus:shadow-neon transition-all duration-300"
                required
              />
            </div>

            <div>
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">
                Coaching License *
              </Label>
              <Select value={formData.license} onValueChange={(value) => setFormData({ ...formData, license: value })}>
                <SelectTrigger className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-vibrant-orange focus:shadow-neon transition-all duration-300">
                  <SelectValue placeholder="Select your license" />
                </SelectTrigger>
                <SelectContent className="bg-card border-border rounded-xl">
                  {licenses.map((license) => (
                    <SelectItem 
                      key={license} 
                      value={license}
                      className="focus:bg-muted/50 focus:text-foreground"
                    >
                      {license}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-vibrant-orange to-hot-pink hover:from-hot-pink hover:to-vibrant-orange text-white font-orbitron font-bold py-3 rounded-2xl transition-all duration-300 hover:shadow-neon hover:-translate-y-1"
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

export default CoachIdentity;