import React, { useEffect } from 'react';

const BackgroundEffects: React.FC = () => {
  useEffect(() => {
    const generateParticles = () => {
      const particlesContainer = document.querySelector('.particles-container');
      if (!particlesContainer) return;

      // Clear existing particles
      particlesContainer.innerHTML = '';

      // Create new particles
      for (let i = 0; i < 40; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + 'vw';
        particle.style.opacity = (Math.random() * 0.8 + 0.2).toString();
        particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
        particle.style.animationDelay = (Math.random() * 5) + 's';
        
        const colors = ['neon-cyan', 'electric-blue', 'hot-pink', 'lime-green'];
        const randomColor = colors[Math.floor(Math.random() * colors.length)];
        particle.style.setProperty('--particle-color', `hsl(var(--${randomColor}))`);
        
        particlesContainer.appendChild(particle);
      }
    };

    generateParticles();
  }, []);

  return (
    <>
      {/* Mesh Background */}
      <div 
        className="fixed inset-0 opacity-10 animate-mesh-move pointer-events-none -z-20"
        style={{
          background: 'var(--gradient-mesh)'
        }}
      />
      
      {/* Grid Overlay */}
      <div 
        className="fixed inset-0 opacity-[0.02] animate-grid-slide pointer-events-none -z-10"
        style={{
          backgroundImage: `
            linear-gradient(45deg, transparent 49%, hsl(var(--neon-cyan) / 0.02) 50%, transparent 51%),
            linear-gradient(-45deg, transparent 49%, hsl(var(--hot-pink) / 0.02) 50%, transparent 51%)
          `,
          backgroundSize: '80px 80px'
        }}
      />
      
      {/* Floating Particles */}
      <div className="particles-container fixed inset-0 pointer-events-none -z-10" />
      
      <style>{`
        .particle {
          position: absolute;
          width: 2px;
          height: 2px;
          background: var(--particle-color);
          border-radius: 50%;
          animation: particle-float 12s infinite linear;
          box-shadow: 0 0 8px var(--particle-color);
        }
      `}</style>
    </>
  );
};

export default BackgroundEffects;