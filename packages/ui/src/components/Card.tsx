import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  className = '',
  onClick,
}) => {
  const isClickable = !!onClick;
  
  return (
    <div
      className={`
        overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/92 shadow-sm backdrop-blur
        ${isClickable ? 'cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg' : ''}
        ${className}
      `}
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={isClickable ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      } : undefined}
    >
      {title && (
        <div className="border-b border-slate-200/80 px-6 py-5">
          <h3 className="text-lg font-semibold tracking-tight text-slate-950">{title}</h3>
        </div>
      )}
      <div className="px-6 py-5">
        {children}
      </div>
    </div>
  );
};
