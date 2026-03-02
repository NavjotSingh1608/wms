import { useAuthStore } from '@/store/auth';

export function useHasPermission(permission: string): boolean {
  const permissions = useAuthStore((s) => s.user?.permissions ?? []);
  return permissions.includes(permission);
}

export function useUserRole(): string {
  return useAuthStore((s) => s.user?.role ?? '');
}
