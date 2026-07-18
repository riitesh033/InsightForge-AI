interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmText = "Confirm",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
  loading = false,
}: ConfirmDialogProps) {
  if (!open) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">

        <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl">

          <h2 className="text-xl font-bold text-foreground">
            {title}
          </h2>

          <p className="mt-3 text-muted-foreground">
            {description}
          </p>

          <div className="mt-8 flex justify-end gap-3">

            <button
              onClick={onCancel}
              disabled={loading}
              className="
                rounded-lg
                border
                border-border
                px-5
                py-2
                text-foreground
                transition
                hover:bg-accent
              "
            >
              {cancelText}
            </button>

            <button
              onClick={onConfirm}
              disabled={loading}
              className="
                rounded-lg
                bg-destructive
                px-5
                py-2
                font-medium
                text-destructive-foreground
                transition
                hover:opacity-90
                disabled:opacity-60
              "
            >
              {loading ? "Please wait..." : confirmText}
            </button>

          </div>

        </div>

      </div>
    </>
  );
}