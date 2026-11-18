import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';
import type { Route, Stop } from '../types';

interface FilterContextType {
  selectedRouteId: string;
  setSelectedRouteId: (id: string) => void;
  selectedStopId: string;
  setSelectedStopId: (id: string) => void;
  routes: Route[];
  stops: Stop[];
  isLoading: boolean;
  refreshData: () => Promise<void>;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export const FilterProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedRouteId, setSelectedRouteId] = useState<string>('all');
  const [selectedStopId, setSelectedStopId] = useState<string>('all');
  const [routes, setRoutes] = useState<Route[]>([]);
  const [stops, setStops] = useState<Stop[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshData = async () => {
    try {
      const [routeList, stopList] = await Promise.allSettled([
        api.getRoutes(),
        api.getStops(),
      ]);

      if (routeList.status === 'fulfilled') {
        setRoutes(routeList.value);
        if (selectedRouteId === 'all' && routeList.value.length > 0) {
          // keep 'all' or default
        }
      }
      if (stopList.status === 'fulfilled') {
        setStops(stopList.value);
      }
    } catch {
      // quiet fail on initial load if unauthenticated
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  return (
    <FilterContext.Provider
      value={{
        selectedRouteId,
        setSelectedRouteId,
        selectedStopId,
        setSelectedStopId,
        routes,
        stops,
        isLoading,
        refreshData,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
};

export const useFilters = () => {
  const ctx = useContext(FilterContext);
  if (!ctx) {
    throw new Error('useFilters must be used within a FilterProvider');
  }
  return ctx;
};
