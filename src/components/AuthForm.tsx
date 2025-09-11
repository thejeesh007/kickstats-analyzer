import React, { useState } from 'react';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { supabase } from '@/integrations/supabase/client';

interface AuthFormProps {
  selectedRole: 'fan' | 'player' | 'coach';
  onBack: () => void;
  onSuccess: (role: 'fan' | 'player' | 'coach') => void;
}

const AuthForm: React.FC<AuthFormProps> = ({ selectedRole, onBack, onSuccess }) => {
  const [activeTab, setActiveTab] = useState<'login' | 'signup'>('login');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success' | 'info'; text: string } | null>(null);
  
  // Form states
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [signupData, setSignupData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email: loginData.email,
        password: loginData.password,
      });

      if (error) {
        setMessage({ type: 'error', text: error.message });
      } else {
        setMessage({ type: 'success', text: 'Login successful! Redirecting...' });
        setTimeout(() => onSuccess(selectedRole), 1000);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Login failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    if (signupData.password !== signupData.confirmPassword) {
      setMessage({ type: 'error', text: "Passwords don't match!" });
      setLoading(false);
      return;
    }

    if (signupData.password.length < 6) {
      setMessage({ type: 'error', text: 'Password must be at least 6 characters long' });
      setLoading(false);
      return;
    }

    try {
      const redirectUrl = `${window.location.origin}/`;
      
      const { error } = await supabase.auth.signUp({
        email: signupData.email,
        password: signupData.password,
        options: {
          emailRedirectTo: redirectUrl,
          data: {
            name: signupData.name,
            role: selectedRole
          }
        }
      });

      if (error) {
        setMessage({ type: 'error', text: error.message });
      } else {
        setMessage({ type: 'success', text: 'Account created! Please check your email to confirm.' });
        setTimeout(() => onSuccess(selectedRole), 2000);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Signup failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const roleColors = {
    fan: 'hot-pink',
    player: 'lime-green',
    coach: 'vibrant-orange'
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
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

          {/* Selected Role Display */}
          <div className="text-center mb-6 pt-6">
            <div className="bg-muted rounded-lg p-3">
              <span className={`font-orbitron font-semibold text-${roleColors[selectedRole]}`}>
                {selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1)} Authentication
              </span>
            </div>
          </div>

          {/* Message */}
          {message && (
            <Alert className={`mb-4 ${
              message.type === 'error' ? 'border-error-red/40 bg-error-red/10' :
              message.type === 'success' ? 'border-success-green/40 bg-success-green/10' :
              'border-electric-blue/40 bg-electric-blue/10'
            }`}>
              <AlertDescription className={
                message.type === 'error' ? 'text-error-red' :
                message.type === 'success' ? 'text-success-green' :
                'text-electric-blue'
              }>
                {message.text}
              </AlertDescription>
            </Alert>
          )}

          {/* Tabs */}
          <div className="flex mb-6 bg-muted/30 rounded-2xl p-1">
            <button
              onClick={() => setActiveTab('login')}
              className={`flex-1 py-2 px-4 rounded-xl font-semibold transition-all duration-300 ${
                activeTab === 'login'
                  ? 'bg-card text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setActiveTab('signup')}
              className={`flex-1 py-2 px-4 rounded-xl font-semibold transition-all duration-300 ${
                activeTab === 'signup'
                  ? 'bg-card text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Forms */}
          {activeTab === 'login' ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="loginEmail" className="text-xs uppercase tracking-wider text-muted-foreground">
                  Email
                </Label>
                <Input
                  id="loginEmail"
                  type="email"
                  placeholder="Enter your email"
                  value={loginData.email}
                  onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                  className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-neon-cyan focus:shadow-neon transition-all duration-300"
                  required
                />
              </div>
              <div>
                <Label htmlFor="loginPassword" className="text-xs uppercase tracking-wider text-muted-foreground">
                  Password
                </Label>
                <Input
                  id="loginPassword"
                  type="password"
                  placeholder="Enter your password"
                  value={loginData.password}
                  onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                  className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-neon-cyan focus:shadow-neon transition-all duration-300"
                  required
                />
              </div>
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-primary hover:bg-gradient-secondary text-white font-orbitron font-bold py-3 rounded-2xl transition-all duration-300 hover:shadow-neon hover:-translate-y-1"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Logging in...
                  </>
                ) : (
                  'Login'
                )}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleSignup} className="space-y-4">
              <div>
                <Label htmlFor="signupName" className="text-xs uppercase tracking-wider text-muted-foreground">
                  Full Name
                </Label>
                <Input
                  id="signupName"
                  type="text"
                  placeholder="Enter your full name"
                  value={signupData.name}
                  onChange={(e) => setSignupData({ ...signupData, name: e.target.value })}
                  className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-neon-cyan focus:shadow-neon transition-all duration-300"
                  required
                />
              </div>
              <div>
                <Label htmlFor="signupEmail" className="text-xs uppercase tracking-wider text-muted-foreground">
                  Email
                </Label>
                <Input
                  id="signupEmail"
                  type="email"
                  placeholder="Enter your email"
                  value={signupData.email}
                  onChange={(e) => setSignupData({ ...signupData, email: e.target.value })}
                  className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-neon-cyan focus:shadow-neon transition-all duration-300"
                  required
                />
              </div>
              <div>
                <Label htmlFor="signupPassword" className="text-xs uppercase tracking-wider text-muted-foreground">
                  Password
                </Label>
                <Input
                  id="signupPassword"
                  type="password"
                  placeholder="Create a password (min 6 characters)"
                  value={signupData.password}
                  onChange={(e) => setSignupData({ ...signupData, password: e.target.value })}
                  className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-neon-cyan focus:shadow-neon transition-all duration-300"
                  minLength={6}
                  required
                />
              </div>
              <div>
                <Label htmlFor="confirmPassword" className="text-xs uppercase tracking-wider text-muted-foreground">
                  Confirm Password
                </Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm your password"
                  value={signupData.confirmPassword}
                  onChange={(e) => setSignupData({ ...signupData, confirmPassword: e.target.value })}
                  className="mt-2 bg-muted/50 border-border rounded-2xl focus:border-neon-cyan focus:shadow-neon transition-all duration-300"
                  required
                />
              </div>
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-primary hover:bg-gradient-secondary text-white font-orbitron font-bold py-3 rounded-2xl transition-all duration-300 hover:shadow-neon hover:-translate-y-1"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  'Sign Up'
                )}
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthForm;