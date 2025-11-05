import { useEffect, useState } from "react";
import { Car } from "lucide-react";
import { cn } from "@/lib/utils";

interface AnimatedCarProps {
  carNumber: string;
  path: number[]; // [start, end] - 0 represents gate
  isExiting: boolean;
}

export const AnimatedCar = ({ carNumber, path, isExiting }: AnimatedCarProps) => {
  const [position, setPosition] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setPosition(1);
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  // Calculate position based on slot number
  const getSlotPosition = (slotNumber: number) => {
    if (slotNumber === 0) {
      // Gate position (left side of slot 1)
      return { top: 128, left: 60 };
    }

    const row = Math.floor((slotNumber - 1) / 5);
    const col = (slotNumber - 1) % 5;
    
    // Base positions with spacing
    const baseTop = 160 + row * 160; // Account for header, spacing, and roads
    const baseLeft = 80 + col * 140; // Account for gate area and spacing
    
    return { top: baseTop, left: baseLeft };
  };

  const startPos = getSlotPosition(path[0]);
  const endPos = getSlotPosition(path[1]);

  const currentTop = startPos.top + (endPos.top - startPos.top) * position;
  const currentLeft = startPos.left + (endPos.left - startPos.left) * position;

  // Calculate rotation based on direction
  const dx = endPos.left - startPos.left;
  const dy = endPos.top - startPos.top;
  const rotation = Math.atan2(dy, dx) * (180 / Math.PI);

  return (
    <div
      className={cn(
        "absolute z-20 transition-all duration-2000 ease-in-out",
        isExiting ? "text-destructive" : "text-primary"
      )}
      style={{
        top: `${currentTop}px`,
        left: `${currentLeft}px`,
        transform: `translate(-50%, -50%) rotate(${rotation}deg)`,
      }}
    >
      <div className="relative">
        <Car className="h-10 w-10 drop-shadow-lg" />
        <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 bg-background/90 px-2 py-0.5 rounded text-xs font-bold whitespace-nowrap border border-border">
          {carNumber}
        </div>
      </div>
    </div>
  );
};
