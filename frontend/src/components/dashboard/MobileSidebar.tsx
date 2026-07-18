import { X } from "lucide-react";

import Sidebar from "./Sidebar";

interface MobileSidebarProps {
  open: boolean;
  onClose: () => void;
}

export default function MobileSidebar({
  open,
  onClose,
}: MobileSidebarProps) {
  return (
    <>
      {/* Overlay */}
      <div
        onClick={onClose}
        className={`
          fixed inset-0 z-40 bg-black/50 transition-opacity duration-300 lg:hidden
          ${
            open
              ? "opacity-100 visible"
              : "opacity-0 invisible"
          }
        `}
      />

      {/* Sidebar */}
      <div
        className={`
          fixed left-0 top-0 z-50 h-full transform transition-transform duration-300 ease-in-out lg:hidden
          ${
            open
              ? "translate-x-0"
              : "-translate-x-full"
          }
        `}
      >
        <div className="relative h-full">

          {/* Close Button */}
          <button
            onClick={onClose}
            className="
              absolute
              right-4
              top-4
              z-50
              rounded-lg
              bg-background
              p-2
              shadow-md
              transition
              hover:bg-accent
            "
          >
            <X size={20} />
          </button>

          {/* Reusable Sidebar */}
          <Sidebar onNavigate={onClose} />

        </div>
      </div>
    </>
  );
}