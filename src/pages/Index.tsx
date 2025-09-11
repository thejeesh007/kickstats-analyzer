import React, { useState, useEffect } from 'react';
import { User, Session } from '@supabase/supabase-js';
import BackgroundEffects from '@/components/BackgroundEffects';
import Navigation from '@/components/Navigation';
import RoleSelection from '@/components/RoleSelection';
import AuthForm from '@/components/AuthForm';
import PlayerIdentity from '@/components/PlayerIdentity';
import CoachIdentity from '@/components/CoachIdentity';
import SuccessScreen from '@/components/SuccessScreen';
import { supabase } from '@/integrations/supabase/client';

type Screen = 'role-selection' | 'auth' | 'player-identity' | 'coach-identity' | 'success';
type Role = 'fan' | 'player' | 'coach';

const Index = () => {
  const [currentScreen, setCurrentScreen] = useState<Screen>('role-selection');
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Set up auth state listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        setLoading(false);
      }
    );

    // Check for existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleRoleSelect = (role: Role) => {
    setSelectedRole(role);
    setCurrentScreen('auth');
  };

  const handleAuthSuccess = async (role: Role) => {
    if (role === 'fan') {
      // For fans, create profile immediately and go to success screen
      try {
        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
          const { error } = await supabase
            .from('profiles')
            .insert({
              id: user.id,
              email: user.email!,
              name: user.user_metadata?.name || 'Fan User',
              role: 'fan'
            });
          
          if (error) {
            console.error('Error creating fan profile:', error);
          }
        }
      } catch (error) {
        console.error('Error:', error);
      }
      setCurrentScreen('success');
    } else {
      // Players and coaches need to complete their identity
      setCurrentScreen(`${role}-identity` as Screen);
    }
  };

  const handleIdentityComplete = () => {
    setCurrentScreen('success');
  };

  const handleBackToRoleSelection = () => {
    setSelectedRole(null);
    setCurrentScreen('role-selection');
  };

  const handleContinueToDashboard = () => {
    // In a real app, this would redirect to the appropriate dashboard
    alert(`Redirecting to ${selectedRole} dashboard...`);
  };

  const renderCurrentScreen = () => {
    switch (currentScreen) {
      case 'role-selection':
        return <RoleSelection onRoleSelect={handleRoleSelect} />;
      
      case 'auth':
        return selectedRole ? (
          <AuthForm
            selectedRole={selectedRole}
            onBack={handleBackToRoleSelection}
            onSuccess={handleAuthSuccess}
          />
        ) : null;
      
      case 'player-identity':
        return (
          <PlayerIdentity
            onBack={handleBackToRoleSelection}
            onComplete={handleIdentityComplete}
          />
        );
      
      case 'coach-identity':
        return (
          <CoachIdentity
            onBack={handleBackToRoleSelection}
            onComplete={handleIdentityComplete}
          />
        );
      
      case 'success':
        return selectedRole ? (
          <SuccessScreen
            role={selectedRole}
            onContinue={handleContinueToDashboard}
          />
        ) : null;
      
      default:
        return <RoleSelection onRoleSelect={handleRoleSelect} />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground font-exo relative overflow-x-hidden flex items-center justify-center">
        <BackgroundEffects />
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-neon-cyan mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // If user is authenticated and has completed setup, show main app with navigation
  if (user && currentScreen === 'success') {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto p-6">
          <div className="text-center py-12">
            <h1 className="text-4xl font-bold mb-4">Welcome to Football Analytics</h1>
            <p className="text-xl text-muted-foreground mb-8">
              Your comprehensive platform for football statistics, analysis, and predictions
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
              <div className="p-6 bg-card rounded-lg border">
                <h3 className="text-lg font-semibold mb-2">Player Statistics</h3>
                <p className="text-muted-foreground">Browse detailed player profiles, career summaries, and performance metrics</p>
              </div>
              <div className="p-6 bg-card rounded-lg border">
                <h3 className="text-lg font-semibold mb-2">Team Analysis</h3>
                <p className="text-muted-foreground">Explore team compositions, statistics, and tactical insights</p>
              </div>
              <div className="p-6 bg-card rounded-lg border">
                <h3 className="text-lg font-semibold mb-2">Match Predictions</h3>
                <p className="text-muted-foreground">AI-powered match forecasts and detailed analysis</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-exo relative overflow-x-hidden">
      <BackgroundEffects />
      {renderCurrentScreen()}
    </div>
  );
};

export default Index;
