import React from 'react';

interface LogoProps {
  /** Size preset for the mark: 'xs' (20px), 'sm' (28px), 'md' (36px), 'lg' (48px), 'xl' (64px) */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  /** Whether to render the accompanying PharmacyGuard text */
  showText?: boolean;
  /** Optional subtitle below the brand title */
  subtitle?: string;
  /** Custom className for the outer container */
  className?: string;
}

const sizeMap = {
  xs: { box: 'w-5 h-5', text: 'text-xs', sub: 'text-[9px]' },
  sm: { box: 'w-7 h-7', text: 'text-sm', sub: 'text-[10px]' },
  md: { box: 'w-9 h-9', text: 'text-base', sub: 'text-xs' },
  lg: { box: 'w-12 h-12', text: 'text-xl', sub: 'text-[13px]' },
  xl: { box: 'w-16 h-16', text: 'text-2xl', sub: 'text-sm' },
};

/**
 * PharmacyGuard Clinical Safety Logo Component
 * Renders the official shield + cross + verification checkmark badge.
 */
export const Logo: React.FC<LogoProps> = ({
  size = 'md',
  showText = false,
  subtitle,
  className = '',
}) => {
  const currentSize = sizeMap[size];

  return (
    <div className={`flex items-center gap-2.5 select-none ${className}`}>
      <div className={`${currentSize.box} shrink-0 flex items-center justify-center relative`}>
        <img
          src="/logo-mark.svg"
          alt="PharmacyGuard Logo"
          className="w-full h-full object-contain drop-shadow-sm transition-transform hover:scale-105 duration-200"
          onError={(e) => {
            // Fallback to PNG if SVG fails to load
            (e.target as HTMLImageElement).src = '/logo-mark.png';
          }}
        />
      </div>

      {showText && (
        <div className="flex flex-col">
          <span className={`font-bold tracking-tight text-[var(--pg-text)] ${currentSize.text} leading-none`}>
            Pharmacy<span className="text-[var(--pg-accent)]">Guard</span>
          </span>
          {subtitle && (
            <span className={`text-[var(--pg-text-muted)] font-medium mt-1 leading-tight ${currentSize.sub}`}>
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
