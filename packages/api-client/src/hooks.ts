import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { EduPilotClient } from './client';
import type { LoginRequest, QueryRequestDto } from '@edupilot/types';

// Query keys
export const queryKeys = {
  courses: ['courses'] as const,
  assignments: (params?: any) => ['assignments', params] as const,
};

// Hooks
export const useEduPilotHooks = (client: EduPilotClient) => {
  const queryClient = useQueryClient();

  // Courses
  const useCourses = () => {
    return useQuery({
      queryKey: queryKeys.courses,
      queryFn: () => client.getCourses(),
    });
  };

  // Assignments
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

  // Login mutation
  const useLogin = () => {
    return useMutation({
      mutationFn: (credentials: LoginRequest) => client.login(credentials),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.courses });
        queryClient.invalidateQueries({ queryKey: queryKeys.assignments() });
      },
    });
  };

  // Sync mutation
  const useSyncData = () => {
    return useMutation({
      mutationFn: () => client.syncData(),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.courses });
        queryClient.invalidateQueries({ queryKey: queryKeys.assignments() });
      },
    });
  };

  // Query mutation
  const useSubmitQuery = () => {
    return useMutation({
      mutationFn: (query: QueryRequestDto) => client.submitQuery(query),
    });
  };

  // Voice query mutation
  const useSubmitVoiceQuery = () => {
    return useMutation({
      mutationFn: (audioFile: File) => client.submitVoiceQuery(audioFile),
    });
  };

  return {
    useCourses,
    useAssignments,
    useLogin,
    useSyncData,
    useSubmitQuery,
    useSubmitVoiceQuery,
  };
};
