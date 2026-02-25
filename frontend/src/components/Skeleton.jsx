import React from 'react';

/**
 * Skeleton Component - Loading placeholder with shimmer effect
 */
const Skeleton = ({ 
  width = '100%', 
  height = '20px', 
  borderRadius = '8px',
  className = '',
  style = {}
}) => {
  return (
    <div
      className={`skeleton ${className}`}
      style={{
        width,
        height,
        borderRadius,
        background: 'linear-gradient(90deg, var(--glass-bg) 25%, rgba(255,255,255,0.1) 50%, var(--glass-bg) 75%)',
        backgroundSize: '200% 100%',
        animation: 'skeleton-shimmer 1.5s ease-in-out infinite',
        ...style,
      }}
    />
  );
};

/**
 * Skeleton Card - Loading card placeholder
 */
export const SkeletonCard = ({ hasTitle = true }) => {
  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1rem' }}>
      {hasTitle && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <Skeleton width="60%" height="24px" />
          <Skeleton width="80px" height="20px" />
        </div>
      )}
      <Skeleton width="100%" height="16px" style={{ marginBottom: '0.5rem' }} />
      <Skeleton width="90%" height="16px" style={{ marginBottom: '0.5rem' }} />
      <Skeleton width="70%" height="16px" />
    </div>
  );
};

/**
 * Skeleton List - Loading list placeholder
 */
export const SkeletonList = ({ items = 3, itemHeight = '60px' }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {Array.from({ length: items }).map((_, index) => (
        <Skeleton 
          key={index} 
          width="100%" 
          height={itemHeight} 
          borderRadius="8px"
        />
      ))}
    </div>
  );
};

/**
 * Skeleton Table - Loading table placeholder
 */
export const SkeletonTable = ({ rows = 5, columns = 3 }) => {
  return (
    <div style={{ width: '100%' }}>
      {/* Header */}
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${columns}, 1fr)`, gap: '1rem', marginBottom: '1rem' }}>
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton key={`header-${index}`} height="20px" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div 
          key={`row-${rowIndex}`}
          style={{ 
            display: 'grid', 
            gridTemplateColumns: `repeat(${columns}, 1fr)`, 
            gap: '1rem', 
            marginBottom: '0.75rem' 
          }}
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={`cell-${rowIndex}-${colIndex}`} height="16px" />
          ))}
        </div>
      ))}
    </div>
  );
};

/**
 * Skeleton Form - Loading form placeholder
 */
export const SkeletonForm = () => {
  return (
    <div>
      <Skeleton width="30%" height="16px" style={{ marginBottom: '0.5rem' }} />
      <Skeleton width="100%" height="48px" style={{ marginBottom: '1.5rem' }} />
      
      <Skeleton width="30%" height="16px" style={{ marginBottom: '0.5rem' }} />
      <Skeleton width="100%" height="120px" style={{ marginBottom: '1.5rem' }} />
      
      <Skeleton width="120px" height="48px" />
    </div>
  );
};

/**
 * Add skeleton animation to global CSS
 */
export const skeletonStyles = `
  @keyframes skeleton-shimmer {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }
`;

export default Skeleton;
