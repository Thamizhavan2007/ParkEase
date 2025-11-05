import { cn } from "@/lib/utils";
import { Car } from "lucide-react";

interface ParkingSlotProps {
  slotNumber: number;
  isOccupied: boolean;
}

export const ParkingSlot = ({ slotNumber, isOccupied }: ParkingSlotProps) => {
  return (
    <div
      className={cn(
        "relative h-24 rounded-lg border-2 transition-all duration-300 flex flex-col items-center justify-center shadow-md",
        isOccupied
          ? "bg-occupied border-occupied text-occupied-foreground"
          : "bg-available border-available text-available-foreground hover:scale-105"
      )}
    >
      <div className="text-xs font-bold mb-1">#{slotNumber}</div>
      {isOccupied && <Car className="h-8 w-8" />}
      {!isOccupied && (
        <div className="text-xs opacity-75">Available</div>
      )}
    </div>
  );
};
