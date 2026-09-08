import { useState } from "react";
import type { Profile, StaffUser, UserRole } from "../types";
import { Button } from "./Button";

interface Props {
  profiles: Profile[];
  initialValue?: StaffUser | null;
  onCancel: () => void;
  onSubmit: (payload: { name: string; email: string; password?: string; role: UserRole; active: boolean }) => Promise<void>;
}

export function UserForm({ profiles, initialValue, onCancel, onSubmit }: Props) {
  const [name, setName] = useState(initialValue?.name ?? "");
  const [email, setEmail] = useState(initialValue?.email ?? "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>(initialValue?.role ?? "CAIXA");
  const [active, setActive] = useState(initialValue?.active ?? true);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await onSubmit({ name, email, password: password || undefined, role, active });
    } finally {
      setSaving(false);
    }
  }

  const selectedProfile = profiles.find((profile) => profile.code === role);

  return (
    <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
      <label className="space-y-2 text-sm">
        <span className="text-slate-600">Nome</span>
        <input required minLength={2} className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={name} onChange={(event) => setName(event.target.value)} />
      </label>
      <label className="space-y-2 text-sm">
        <span className="text-slate-600">E-mail</span>
        <input required type="email" className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={email} onChange={(event) => setEmail(event.target.value)} />
      </label>
      <label className="space-y-2 text-sm">
        <span className="text-slate-600">Perfil</span>
        <select className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
          {profiles.map((profile) => <option key={profile.id} value={profile.code}>{profile.name}</option>)}
        </select>
      </label>
      <label className="space-y-2 text-sm">
        <span className="text-slate-600">{initialValue ? "Nova senha (opcional)" : "Senha"}</span>
        <input required={!initialValue} minLength={6} type="password" className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={password} onChange={(event) => setPassword(event.target.value)} />
      </label>
      <div className="rounded-2xl border border-stroke bg-brand/4 p-4 text-sm text-slate-600 md:col-span-2">
        <p className="font-medium text-brandDeeper">Acesso do perfil</p>
        <p className="mt-2">{selectedProfile?.permissions.map((permission) => permission.name).join(" • ")}</p>
      </div>
      <label className="flex items-center gap-3 text-sm text-slate-600 md:col-span-2">
        <input type="checkbox" checked={active} onChange={(event) => setActive(event.target.checked)} />
        Usuário ativo
      </label>
      <div className="flex justify-end gap-3 md:col-span-2">
        <Button type="button" variant="ghost" onClick={onCancel}>Cancelar</Button>
        <Button type="submit" disabled={saving}>{saving ? "Salvando..." : "Salvar usuário"}</Button>
      </div>
    </form>
  );
}
