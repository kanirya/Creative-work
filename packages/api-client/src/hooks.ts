import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { EduPilotClient } from './client';
import type { LoginRequest, QueryRequestDto } from '@edupilot/types';

// Query keys
export const queryKeys = {
  courses: ['courses'] as const,
  assignments: (params?: any) => ['assignments', params] as const,
};

// Create a global client instance (will be set by the app)
let globalClient: EduPilotClient | null = null;

export const setGlobalClient = (client: EduPilotClient) => {
  globalClient = client;
};

const getClient = () => {
  if (!globalClient) {
    throw new Error('EduPilot client not initialized. Call setGlobalClient first.');
  }
  return globalClient;
};

// Individual hooks that can be imported directly
export const useStudentCourses = () => {
  return useQuery({
    queryKey: queryKeys.courses,
    queryFn: () => getClient().getCourses(),
  });
};

export const useStudentAssignments = (params?: {
  status?: string;
  upcomingOnly?: boolean;
  daysAhead?: number;
}) => {
  return useQuery({
    queryKey: queryKeys.assignments(params),
    queryFn: () => getClient().getAssignments(params),
  });
};

export const useLogin = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (credentials: LoginRequest) => getClient().login(credentials),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.courses });
      queryClient.invalidateQueries({ queryKey: queryKeys.assignments() });
    },
  });
};

export const useSyncData = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => getClient().syncData(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.courses });
      queryClient.invalidateQueries({ queryKey: queryKeys.assignments() });
    },
  });
};

export const useSubmitQuery = () => {
  return useMutation({
    mutationFn: (query: QueryRequestDto) => getClient().submitQuery(query),
  });
};

export const useSubmitVoiceQuery = () => {
  return useMutation({
    mutationFn: (audioFile: File) => getClient().submitVoiceQuery(audioFile),
  });
};

// Legacy factory function for backward compatibility
export const useEduPilotHooks = (client: EduPilotClient) => {
  const queryClient = useQueryClient();

  const useCourses = () => {
    return useQuery({
      queryKey: queryKeys.courses,
      queryFn: () => client.getCourses(),
    });
  };

  const useAssignments = (params?: {
    status?: string;
    upcomingOnly?: boolean;
    daysAhead?: number;
  }) => {
    return useQuery({
      queryKey: queryKeys.assignments(params),
      queryFn: () => client.getAssignments(params),
    });
  };

  const useLoginMutation = () => {
    return useMutation({
      mutationFn: (credentials: LoginRequest) => client.login(credentials),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.courses });
        queryClient.invalidateQueries({ queryKey: queryKeys.assignments() });
      },
    });
  };

  const useSyncDataMutation = () => {
    return useMutation({
      mutationFn: () => client.syncData(),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.courses });
        queryClient.invalidateQueries({ queryKey: queryKeys.assignments() });
      },
    });
  };

  const useSubmitQueryMutation = () => {
    return useMutation({
      mutationFn: (query: QueryRequestDto) => client.submitQuery(query),
    });
  };

  const useSubmitVoiceQueryMutation = () => {
    return useMutation({
      mutationFn: (audioFile: File) => client.submitVoiceQuery(audioFile),
    });
  };

  return {
    useCourses,
    useAssignments,
    useLogin: useLoginMutation,
    useSyncData: useSyncDataMutation,
    useSubmitQuery: useSubmitQueryMutation,
    useSubmitVoiceQuery: useSubmitVoiceQueryMutation,
  };
};
