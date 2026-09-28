"use client";

import React, { useState } from "react";
import { DetectedFace } from "@/types";
import { cn } from "@/lib/utils";
import { Check, AlertTriangle, HelpCircle } from "lucide-react";

interface FaceOverlayProps {
  imageUrl: string;
  faces: DetectedFace[];
  onSelectFace?: (face: DetectedFace) => void;
  selectedBoxId?: string | null;
}

export const FaceOverlay: React.FC<FaceOverlayProps> = ({
  imageUrl,
  faces,
  onSelectFace,
  selectedBoxId,
}) => {
  const [hoveredBoxId, setHoveredBoxId] = useState<string | null>(null);

  const recognizedCount = faces.filter((f) => f.status === "recognized").length;
  const reviewCount = faces.filter((f) => f.status === "review").length;
  const unknownCount = faces.filter((f) => f.status === "unknown").length;

  return (
    <div className="bg-white border border-border rounded-card p-4 text-left">
      {/* Metric Summary Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-3 border-b border-border text-[13px]">
        <div className="flex items-center gap-4">
          <div>
            <span className="text-secondary-text">Detected: </span>
            <span className="font-semibold text-primary-text">{faces.length}</span>
          </div>
          <div className="flex items-center gap-1.5 text-success">
            <span className="w-2 h-2 rounded-full bg-success" />
            <span>Recognized: </span>
            <span className="font-semibold">{recognizedCount}</span>
          </div>
          {reviewCount > 0 && (
            <div className="flex items-center gap-1.5 text-warning">
              <span className="w-2 h-2 rounded-full bg-warning" />
              <span>Needs Review: </span>
              <span className="font-semibold">{reviewCount}</span>
            </div>
          )}
          {unknownCount > 0 && (
            <div className="flex items-center gap-1.5 text-secondary-text">
              <span className="w-2 h-2 rounded-full bg-[#9CA3AF]" />
              <span>Unknown: </span>
              <span className="font-semibold">{unknownCount}</span>
            </div>
          )}
        </div>
        <div className="text-[11px] text-muted-text">
          Click any face box to inspect or correct
        </div>
      </div>

      {/* Image with SVG/Absolute Bounding Boxes */}
      <div className="relative w-full rounded-control overflow-hidden bg-black/5 aspect-video border border-border/70 select-none">
        <img
          src={imageUrl}
          alt="Classroom photo detection"
          className="w-full h-full object-contain pointer-events-none"
        />

        {/* Bounding Boxes Layer */}
        {faces.map((face) => {
          const isSelected = selectedBoxId === face.box_id;
          const isHovered = hoveredBoxId === face.box_id;

          // Subtle unobtrusive color styling
          let borderColor = "border-[#9CA3AF]";
          let labelBg = "bg-[#374151]";
          let textColor = "text-white";

          if (face.status === "recognized") {
            borderColor = "border-[#16803C]";
            labelBg = "bg-[#16803C]";
          } else if (face.status === "review") {
            borderColor = "border-[#B7791F]";
            labelBg = "bg-[#B7791F]";
          }

          return (
            <div
              key={face.box_id}
              onClick={() => onSelectFace && onSelectFace(face)}
              onMouseEnter={() => setHoveredBoxId(face.box_id)}
              onMouseLeave={() => setHoveredBoxId(null)}
              style={{
                left: `${face.bbox.x}%`,
                top: `${face.bbox.y}%`,
                width: `${face.bbox.width}%`,
                height: `${face.bbox.height}%`,
              }}
              className={cn(
                "absolute border cursor-pointer transition-all duration-100",
                borderColor,
                isSelected ? "border-2 ring-2 ring-accent/50 z-20" : "border",
                isHovered && "border-2 z-10"
              )}
            >
              {/* Compact unobtrusive tag label placed directly above or inside top */}
              <div
                className={cn(
                  "absolute -top-6 left-0 px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap shadow-sm flex items-center gap-1",
                  labelBg,
                  textColor
                )}
              >
                {face.status === "recognized" && <Check className="w-2.5 h-2.5" />}
                {face.status === "review" && <AlertTriangle className="w-2.5 h-2.5" />}
                {face.status === "unknown" && <HelpCircle className="w-2.5 h-2.5" />}
                <span>
                  {face.student_name ? face.student_name.split(" ")[0] : "Unknown"}
                </span>
                {face.confidence > 0 && (
                  <span className="opacity-90 tabular-nums">
                    {(face.confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
