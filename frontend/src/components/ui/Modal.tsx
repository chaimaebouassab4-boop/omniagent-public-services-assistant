import { X } from "lucide-react";
import { type ReactNode } from "react";
import { Button } from "./Button";

interface ModalProps {
  title: string;
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
}

/** Accessible modal dialog shell for focused admin actions. */
export function Modal({ title, isOpen, onClose, children }: ModalProps): JSX.Element | null {
  if (!isOpen) {
    return null;
  }

  return (
    <div
      aria-modal="true"
      role="dialog"
      aria-labelledby="modal-title"
      className="fixed inset-0 z-50 grid place-items-center bg-slate-950/45 p-4"
    >
      <div className="w-full max-w-lg rounded-lg bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-border p-5">
          <h2 id="modal-title" className="text-lg font-bold text-slate-950">
            {title}
          </h2>
          <Button variant="ghost" size="icon" type="button" onClick={onClose} aria-label="Close">
            <X className="h-5 w-5" aria-hidden="true" />
          </Button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}
