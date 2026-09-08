import { api } from "./api";
import type { AuditLog, Profile, StaffUser, UserRole } from "../types";

export interface StaffPayload {
  name: string;
  email: string;
  password?: string;
  role: UserRole;
  active: boolean;
}

export const administrationService = {
  listUsers: async () => (await api.get<StaffUser[]>("/users")).data,
  createUser: async (payload: StaffPayload) => (await api.post<StaffUser>("/users", payload)).data,
  updateUser: async (id: number, payload: StaffPayload) => (await api.put<StaffUser>(`/users/${id}`, payload)).data,
  listProfiles: async () => (await api.get<Profile[]>("/profiles")).data,
  listAudit: async (entityType?: string) =>
    (await api.get<AuditLog[]>("/audit", { params: { entity_type: entityType || undefined, limit: 100 } })).data,
};
