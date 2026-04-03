// Helper to generate breadcrumbs from current route
export const generateBreadcrumbs = (pathname) => {
  const paths = pathname.split('/').filter(Boolean);
  
  const breadcrumbs = [
    { label: 'Home', path: '/' },
  ];

  let currentPath = '';
  
  paths.forEach((path) => {
    currentPath += `/${path}`;
    const label = path.charAt(0).toUpperCase() + path.slice(1).replace(/-/g, ' ');
    breadcrumbs.push({
      label: label,
      path: currentPath,
    });
  });

  return breadcrumbs;
};