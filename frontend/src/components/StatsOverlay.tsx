import { Card, CardContent } from "@/components/ui/card";
import { ParkingStats } from "@/pages/Index";
import { TrendingUp, Users, Clock } from "lucide-react";

interface StatsOverlayProps {
  stats: ParkingStats;
}

export const StatsOverlay = ({ stats }: StatsOverlayProps) => {
  return (
    <div className="absolute bottom-6 left-6 right-6">
      <Card className="bg-card/95 backdrop-blur-sm border-primary/20 shadow-xl">
        <CardContent className="py-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-3">
              <div className="bg-primary/10 p-3 rounded-lg">
                <TrendingUp className="h-6 w-6 text-primary" />
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Occupied Slots</div>
                <div className="text-2xl font-bold text-foreground">
                  {stats.total_parked} / 20
                </div>
                <div className="text-xs text-muted-foreground">
                  {stats.occupancy_percentage.toFixed(0)}% Full
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="bg-warning/10 p-3 rounded-lg">
                <Users className="h-6 w-6 text-warning" />
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Cars in Queue</div>
                <div className="text-2xl font-bold text-foreground">
                  {stats.queue_length}
                </div>
                <div className="text-xs text-muted-foreground">
                  Waiting to park
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="bg-accent/10 p-3 rounded-lg">
                <Clock className="h-6 w-6 text-accent" />
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Avg. Wait Time</div>
                <div className="text-2xl font-bold text-foreground">
                  {stats.average_wait_time.toFixed(1)}
                </div>
                <div className="text-xs text-muted-foreground">
                  minutes
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
