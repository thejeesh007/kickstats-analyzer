import { Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Home, Users, Shield, Calendar, Target, BarChart } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/players', label: 'Players', icon: Users },
    { path: '/teams', label: 'Teams', icon: Shield },
    { path: '/matches', label: 'Matches', icon: Calendar },
    { path: '/predictions', label: 'Predictions', icon: Target },
    { path: '/analysis', label: 'Analysis', icon: BarChart },
  ];

  return (
    <nav className="bg-card border-b border-border p-4">
      <div className="container mx-auto flex items-center justify-between">
        <h1 className="text-2xl font-bold text-primary">Football Analytics</h1>
        
        <div className="flex gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Button
                key={item.path}
                variant={isActive ? 'default' : 'ghost'}
                asChild
                className="flex items-center gap-2"
              >
                <Link to={item.path}>
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              </Button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;