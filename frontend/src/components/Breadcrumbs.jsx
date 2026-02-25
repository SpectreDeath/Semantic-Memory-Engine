import React from 'react';
import { ChevronRight, Home } from 'lucide-react';

/**
 * Breadcrumbs Component
 * Navigation trail showing current location
 */
const Breadcrumbs = ({ items = [], onNavigate }) => {
  if (!items || items.length === 0) {
    return null;
  }

  const getIcon = (index) => {
    if (index === 0) return Home;
    return null;
  };

  return (
    <nav
      aria-label="Breadcrumb"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        fontSize: '0.875rem',
        color: 'var(--text-secondary)',
        marginBottom: '1rem',
      }}
    >
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        const Icon = getIcon(index);

        return (
          <React.Fragment key={item.path || index}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              {Icon && (
                <Icon
                  size={16}
                  style={{ cursor: isLast ? 'default' : 'pointer' }}
                  onClick={isLast ? undefined : () => onNavigate?.(item)}
                />
              )}
              <span
                style={{
                  cursor: isLast ? 'default' : 'pointer',
                  color: isLast ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontWeight: isLast ? 500 : 400,
                  transition: 'color 0.2s',
                }}
                onClick={isLast ? undefined : () => onNavigate?.(item)}
              >
                {item.label}
              </span>
            </div>
            {!isLast && (
              <ChevronRight size={14} color="var(--text-secondary)" />
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

// Helper to generate breadcrumbs from current route
export const generateBreadcrumbs = (pathname) => {
  const paths = pathname.split('/').filter(Boolean);
  
  const breadcrumbs = [
    { label: 'Home', path: '/' },
  ];

  let currentPath = '';
  paths.forEach((segment) => {
    currentPath += `/${segment}`;
    breadcrumbs.push({
      label: segment.charAt(0).toUpperCase() + segment.slice(1),
      path: currentPath,
    });
  });

  return breadcrumbs;
};

export default Breadcrumbs;
