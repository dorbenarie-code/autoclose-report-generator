import React from 'react';
 
export const Loader: React.FC = () => {
  return (
    <div className="flex items-center justify-center p-4" data-testid="loader">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
  );
}; 