import { Artifact } from '@/types';

// Placeholder for Supabase client
// import { createClient } from '@/utils/supabase/client';

export async function getArtifacts(): Promise<Artifact[]> {
  // const supabase = createClient();
  // const { data, error } = await supabase.from('artifacts').select('*');
  // if (error) throw error;
  // return data as Artifact[];
  return [];
}

export async function getArtifactById(id: string): Promise<Artifact | null> {
  // const supabase = createClient();
  // const { data, error } = await supabase.from('artifacts').select('*').eq('id', id).single();
  // if (error) throw error;
  // return data as Artifact;
  return null;
}
