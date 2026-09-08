import { useEffect, useState } from "react";
import type { Category } from "../types";
import { Button } from "./Button";

export function CategoryForm({ initialValue, onCancel, onSubmit }: {
  initialValue?: Category | null;
  onCancel: () => void;
  onSubmit: (payload: { name: string; description: string }) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setName(initialValue?.name ?? "");
    setDescription(initialValue?.description ?? "");
  }, [initialValue]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await onSubmit({ name, description });
    } finally {
      setSaving(false);
    }
  }

  return <form className="space-y-4" onSubmit={submit}>
    <label className="block space-y-2 text-sm">
      <span className="text-slate-600">Nome</span>
      <input required minLength={2} maxLength={100} className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={name} onChange={(event) => setName(event.target.value)} />
    </label>
    <label className="block space-y-2 text-sm">
      <span className="text-slate-600">Descrição</span>
      <textarea rows={3} className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={description} onChange={(event) => setDescription(event.target.value)} />
    </label>
    <div className="flex justify-end gap-3">
      <Button type="button" variant="ghost" onClick={onCancel}>Cancelar</Button>
      <Button type="submit" disabled={saving}>{saving ? "Salvando..." : "Salvar categoria"}</Button>
    </div>
  </form>;
}
