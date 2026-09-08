import type { PropsWithChildren } from "react";

export function Modal({ title, children, onClose }: PropsWithChildren<{ title: string; onClose: () => void }>) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#011142]/18 backdrop-blur-sm p-4" onClick={onClose}>
      <div className="glass-panel w-full max-w-2xl rounded-3xl p-6" onClick={(event) => event.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-xl font-semibold text-brandDeeper">{title}</h3>
          <button className="rounded-full bg-brand/8 p-2 text-brandDark" onClick={onClose}>
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
