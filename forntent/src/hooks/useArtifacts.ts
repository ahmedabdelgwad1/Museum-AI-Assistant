import { useState, useEffect } from 'react';
import { Artifact } from '@/types';
// import { getArtifacts } from '@/lib/api/artifacts'; // To be implemented

export function useArtifacts() {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchArtifacts() {
      try {
        // Placeholder for actual Supabase fetch
        // const data = await getArtifacts();
        // setArtifacts(data);
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch artifacts'));
        setIsLoading(false);
      }
    }

    fetchArtifacts();
  }, []);

  return {
    artifacts,
    isLoading,
    error
  };
}
