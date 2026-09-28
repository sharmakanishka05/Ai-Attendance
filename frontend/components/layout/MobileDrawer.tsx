"use client";

import React from "react";
import { Sidebar } from "./Sidebar";
import { X } from "lucide-react";

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MobileDrawer: React.FC<MobileDrawerProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-[2px] transition-opacity"
        onClick={onClose}
      />
      <div className="fixed inset-y-0 left-0 max-w-xs w-full bg-white shadow-xl z-10 flex">
        <Sidebar onCloseMobile={onClose} className="w-full border-none" />
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-secondary-text hover:text-primary-text"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};
