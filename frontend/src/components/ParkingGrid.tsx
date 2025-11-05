import { ParkingSlot } from "@/components/ParkingSlot";
import { AnimatedCar } from "@/components/AnimatedCar";
import { AnimatingCar } from "@/pages/Index";

interface ParkingGridProps {
  occupiedSlots: Set<number>;
  animatingCar: AnimatingCar | null;
}

export const ParkingGrid = ({ occupiedSlots, animatingCar }: ParkingGridProps) => {
  const totalSlots = 20;
  const columns = 5;
  const rows = 4;

  const slots = Array.from({ length: totalSlots }, (_, i) => i + 1);

  return (
    <div className="bg-card rounded-xl shadow-lg p-6 border border-border relative min-h-[600px]">
      <h2 className="text-xl font-semibold mb-6 text-foreground">Parking Lot Map</h2>
      
      {/* Gate indicator */}
      <div className="absolute left-2 top-32 z-10">
        <div className="bg-gate text-gate-foreground px-3 py-2 rounded-lg font-bold text-sm shadow-md border-2 border-gate">
          GATE
        </div>
      </div>

      <div className="space-y-8 relative">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="relative">
            {/* Road */}
            {rowIndex < rows - 1 && (
              <div className="absolute left-0 right-0 h-12 bg-road -bottom-6 rounded">
                <div className="absolute top-1/2 left-0 right-0 h-0.5 border-t-2 border-dashed border-road-line transform -translate-y-1/2" />
              </div>
            )}
            
            {/* Slots Row */}
            <div className="grid grid-cols-5 gap-4 relative z-10">
              {slots
                .slice(rowIndex * columns, (rowIndex + 1) * columns)
                .map((slotNumber) => (
                  <ParkingSlot
                    key={slotNumber}
                    slotNumber={slotNumber}
                    isOccupied={occupiedSlots.has(slotNumber)}
                  />
                ))}
            </div>
          </div>
        ))}
      </div>

      {/* Animated Car */}
      {animatingCar && (
        <AnimatedCar
          carNumber={animatingCar.carNumber}
          path={animatingCar.path}
          isExiting={animatingCar.isExiting}
        />
      )}
    </div>
  );
};
