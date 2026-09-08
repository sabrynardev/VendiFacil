import { Pencil, Plus } from "lucide-react";
import { useState } from "react";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { useToast } from "../components/ToastProvider";
import { UserForm } from "../components/UserForm";
import { useAsync } from "../hooks/useAsync";
import { administrationService, type StaffPayload } from "../services/administration";
import type { StaffUser } from "../types";

export function UsersPage() {
  const toast = useToast();
  const { data, loading, error, setData } = useAsync(async () => {
    const [users, profiles] = await Promise.all([administrationService.listUsers(), administrationService.listProfiles()]);
    return { users, profiles };
  }, []);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<StaffUser | null>(null);

  function closeModal() {
    setOpen(false);
    setEditing(null);
  }

  async function handleSubmit(payload: StaffPayload) {
    try {
      const saved = editing
        ? await administrationService.updateUser(editing.id, payload)
        : await administrationService.createUser({ ...payload, password: payload.password ?? "" });
      setData((current) => current ? {
        ...current,
        users: editing
          ? current.users.map((user) => user.id === saved.id ? saved : user)
          : [...current.users, saved].sort((a, b) => a.name.localeCompare(b.name)),
      } : current);
      toast.push(editing ? "Usuário atualizado com sucesso." : "Usuário criado com sucesso.");
      closeModal();
    } catch (error) {
      toast.push(error instanceof Error ? error.message : "Não foi possível salvar o usuário.", "error");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="page-title">Equipe</h1>
          <p className="page-subtitle">Usuários e perfis de acesso do estabelecimento.</p>
        </div>
        <Button onClick={() => setOpen(true)}><Plus size={16} className="mr-2" />Novo usuário</Button>
      </div>
      <Card>
        {loading ? <p className="text-sm text-slate-500">Carregando equipe...</p> : error ? (
          <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>
        ) : !data?.users.length ? (
          <EmptyState title="Nenhum usuário cadastrado" description="Cadastre quem terá acesso ao sistema." />
        ) : (
          <DataTable headers={["Nome", "E-mail", "Perfil", "Status", "Ações"]}>
            {data.users.map((user) => (
              <tr key={user.id}>
                <td className="px-4 py-3 font-medium">{user.name}</td>
                <td className="px-4 py-3 text-slate-600">{user.email}</td>
                <td className="px-4 py-3">{user.profile_name}</td>
                <td className="px-4 py-3"><Badge label={user.active ? "ATIVO" : "INATIVO"} /></td>
                <td className="px-4 py-3">
                  <Button variant="ghost" onClick={() => { setEditing(user); setOpen(true); }}><Pencil size={16} /></Button>
                </td>
              </tr>
            ))}
          </DataTable>
        )}
      </Card>
      {open && data && (
        <Modal title={editing ? "Editar usuário" : "Novo usuário"} onClose={closeModal}>
          <UserForm profiles={data.profiles} initialValue={editing} onCancel={closeModal} onSubmit={handleSubmit} />
        </Modal>
      )}
    </div>
  );
}
