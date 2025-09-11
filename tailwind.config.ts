import type { Config } from "tailwindcss";

export default {
	darkMode: ["class"],
	content: [
		"./pages/**/*.{ts,tsx}",
		"./components/**/*.{ts,tsx}",
		"./app/**/*.{ts,tsx}",
		"./src/**/*.{ts,tsx}",
	],
	prefix: "",
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px'
			}
		},
		extend: {
			fontFamily: {
				'orbitron': ['Orbitron', 'monospace'],
				'exo': ['Exo 2', 'sans-serif'],
			},
			colors: {
				// Neon colors
				'neon-cyan': 'hsl(var(--neon-cyan))',
				'electric-blue': 'hsl(var(--electric-blue))',
				'deep-purple': 'hsl(var(--deep-purple))',
				'vibrant-orange': 'hsl(var(--vibrant-orange))',
				'hot-pink': 'hsl(var(--hot-pink))',
				'lime-green': 'hsl(var(--lime-green))',
				'midnight': 'hsl(var(--midnight))',
				'dark-slate': 'hsl(var(--dark-slate))',
				'success-green': 'hsl(var(--success-green))',
				'warning-orange': 'hsl(var(--warning-orange))',
				'error-red': 'hsl(var(--error-red))',
				
				// Design system colors
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
			},
			backgroundImage: {
				'gradient-mesh': 'var(--gradient-mesh)',
				'gradient-primary': 'var(--gradient-primary)',
				'gradient-secondary': 'var(--gradient-secondary)',
				'gradient-accent': 'var(--gradient-accent)',
			},
			boxShadow: {
				'neon': 'var(--shadow-neon) hsl(var(--neon-cyan) / 0.4)',
				'neon-blue': 'var(--shadow-neon) hsl(var(--electric-blue) / 0.4)',
				'neon-pink': 'var(--shadow-neon) hsl(var(--hot-pink) / 0.4)',
				'glass': 'var(--shadow-glass)',
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			},
			keyframes: {
				'accordion-down': {
					from: {
						height: '0'
					},
					to: {
						height: 'var(--radix-accordion-content-height)'
					}
				},
				'accordion-up': {
					from: {
						height: 'var(--radix-accordion-content-height)'
					},
					to: {
						height: '0'
					}
				},
				'mesh-move': {
					'0%, 100%': { transform: 'scale(1) rotate(0deg)' },
					'33%': { transform: 'scale(1.1) rotate(120deg)' },
					'66%': { transform: 'scale(0.9) rotate(240deg)' },
				},
				'grid-slide': {
					'0%': { transform: 'translate(0, 0)' },
					'100%': { transform: 'translate(80px, 80px)' },
				},
				'particle-float': {
					'0%': {
						transform: 'translateY(100vh) rotate(0deg)',
						opacity: '0',
					},
					'10%': {
						opacity: '1',
					},
					'90%': {
						opacity: '1',
					},
					'100%': {
						transform: 'translateY(-100px) rotate(360deg)',
						opacity: '0',
					},
				},
				'fade-in': {
					'0%': { opacity: '0', transform: 'translateY(10px)' },
					'100%': { opacity: '1', transform: 'translateY(0)' },
				},
				'glow': {
					'0%, 100%': { 
						boxShadow: '0 0 20px hsl(var(--neon-cyan) / 0.2)' 
					},
					'50%': { 
						boxShadow: '0 0 40px hsl(var(--neon-cyan) / 0.6)' 
					},
				}
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out',
				'mesh-move': 'mesh-move 20s ease-in-out infinite',
				'grid-slide': 'grid-slide 25s linear infinite',
				'particle-float': 'particle-float 12s infinite linear',
				'fade-in': 'fade-in 0.5s ease',
				'glow': 'glow 2s ease-in-out infinite',
			}
		}
	},
	plugins: [require("tailwindcss-animate")],
} satisfies Config;
