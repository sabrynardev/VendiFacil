import { useEffect, useState } from "react";
import type { Supplier } from "../types";
import { Button } from "./Button";

export function SupplierForm({
  initialValue,
  onSubmit,
  onCancel,
}: {
  initialValue?: Supplier | null;
  onSubmit: (payload: Record<string, unknown>) => Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    name: "",
    cnpj: "",
    phone: "",
    whatsapp: "",
    email: "",
    address: "",
    notes: "",
  });

  useEffect(() => {
    if (initialValue) {
      setForm({
        name: initialValue.name,
        cnpj: initialValue.cnpj ?? "",
        phone: initialValue.phone ?? "",
        whatsapp: initialValue.whatsapp ?? "",
        email: initialValue.email ?? "",
        address: initialValue.address ?? "",
        notes: initialValue.notes ?? "",
      });
    }
  }, [initialValue]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    await onSubmit(form);
  }

  return (
    <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
      {[
        ["name", "Nome"],
        ["cnpj", "CNPJ"],
        ["phone", "Telefone"],
        ["whatsapp", "WhatsApp"],
        ["email", "E-mail"],
      ].map(([name, label]) => (
        <label key={name} className="space-y-2 text-sm">
          <span>{label}</span>
          <input
            required={name === "name"}
            className="w-full rounded-xl border-stroke bg-slate-900/70 text-slate-100"
            value={form[name as keyof typeof form]}
            onChange={(event) => setForm((current) => ({ ...current, [name]: event.target.value }))}
          />
        </label>
      ))}
      <label className="space-y-2 text-sm md:col-span-2">
        <span>Endereço</span>
        <input
          className="w-full rounded-xl border-stroke bg-slate-900/70 text-slate-100"
          value={form.address}
          onChange={(event) => setForm((current) => ({ ...current, address: event.target.value }))}
        />
      </label>
      <label className="space-y-2 text-sm md:col-span-2">
        <span>Observações</span>
        <textarea
          rows={3}
          className="w-full rounded-xl border-stroke bg-slate-900/70 text-slate-100"
          value={form.notes}
          onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
        />
      </label>
      <div className="flex items-center justify-end gap-3 md:col-span-2">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit">Salvar fornecedor</Button>
      </div>
    </form>
  );
}
