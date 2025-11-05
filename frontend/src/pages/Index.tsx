import { useState, useEffect } from "react";
import { AddCarForm } from "@/components/AddCarForm";
import { ExitCarForm } from "@/components/ExitCarForm";
import { StatusCheck } from "@/components/StatusCheck";
import { ParkingGrid } from "@/components/ParkingGrid";
import { StatsOverlay } from "@/components/StatsOverlay";
import { toast } from "sonner";

export interface ParkingStats {
  total_parked: number;
  occupancy_percentage: number;
  revenue: number;
  average_wait_time: number;
  queue_length: number;
  current_rate: number;
}

export interface AnimatingCar {
  carNumber: string;
  path: number[];
  isExiting: boolean;
}

const Index = () => {
  const [stats, setStats] = useState<ParkingStats>({
    total_parked: 0,
    occupancy_percentage: 0,
    revenue: 0,
    average_wait_time: 0,
    queue_length: 0,
    current_rate: 1,
  });
  const [occupiedSlots, setOccupiedSlots] = useState<Set<number>>(new Set());
  const [animatingCar, setAnimatingCar] = useState<AnimatingCar | null>(null);
  const [apiBaseUrl, setApiBaseUrl] = useState("http://127.0.0.1:8000");

  const fetchStats = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/status`);
      if (response.ok) {
        const data = await response.json();
        // Convert the backend data format to our frontend stats format
        const occupied = data.slots?.filter(s => s.occupied).length || 0;
        const total = data.slots?.length || 0;
        
        setStats({
          total_parked: data.stats?.total_parked || 0,
          occupancy_percentage: total ? (occupied / total) * 100 : 0,
          revenue: data.stats?.revenue || 0,
          average_wait_time: data.stats?.avg_wait_seconds || 0,
          queue_length: data.queue_length || 0,
          current_rate: data.pricing_rate_per_min || 1,
        });
      }
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const fetchVisualization = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/visualization`);
      if (response.ok) {
        const data = await response.json();
        if (data.stats) {
          setStats(data.stats);
        }
        // Parse grid to get occupied slots
        if (data.grid) {
          const slots = new Set<number>();
          const rows = data.grid.split('\n');
          let slotNumber = 1;
          for (const row of rows) {
            const cells = row.trim().split(/\s+/);
            for (const cell of cells) {
              if (cell === 'X') {
                slots.add(slotNumber);
              }
              slotNumber++;
            }
          }
          setOccupiedSlots(slots);
        }
      }
    } catch (error) {
      console.error("Error fetching visualization:", error);
    }
  };

  useEffect(() => {
    fetchVisualization();
    const interval = setInterval(fetchVisualization, 3000);
    return () => clearInterval(interval);
  }, [apiBaseUrl]);

const handleCarEntry = async (carNumber: string) => {
  try {
    const response = await fetch(`${apiBaseUrl}/entry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ car_number: carNumber }), // ✅ send JSON body
    });

    const data = await response.json();

    if (response.ok) {
      toast.success(`Car ${carNumber} added successfully`);
      
      // Try to extract slot number from response if available
      const slotMatch = data.message?.match(/slot (\d+)/i);
      if (slotMatch) {
        const slotNumber = parseInt(slotMatch[1]);
        setAnimatingCar({
          carNumber,
          path: [0, slotNumber], // 0 represents gate
          isExiting: false,
        });

        setTimeout(() => {
          setAnimatingCar(null);
          fetchVisualization();
        }, 2000);
      } else {
        fetchVisualization();
      }
    } else {
      toast.error(data.detail || data.message || "Failed to park car");
    }
  } catch (error) {
    toast.error("Failed to add car");
    console.error(error);
  }
};


// const handleCarExit = async (carNumber: string) => {
//   try {
//     const response = await fetch(`${apiBaseUrl}/exit`, {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ car_number: carNumber }), // ✅ send JSON body
//     });

//     const data = await response.json();

//     if (response.ok) {
//       const chargeMatch = data.message?.match(/Charge: ₹([\d.]+)/);
//       if (chargeMatch) {
//         const charge = chargeMatch[1];
//         toast.success(`Car ${carNumber} exited. Charge: ₹${charge}`);
//       } else {
//         toast.success(`Car ${carNumber} exited successfully`);
//       }

//       // Optional animation if slot known
//       const currentSlot = Array.from(occupiedSlots).find(slot => true);
//       if (currentSlot) {
//         setAnimatingCar({
//           carNumber,
//           path: [currentSlot, 0], // Exit to gate (0)
//           isExiting: true,
//         });

//         setTimeout(() => {
//           setAnimatingCar(null);
//           fetchVisualization();
//         }, 2000);
//       } else {
//         fetchVisualization();
//       }
//     } else {
//       toast.error(data.detail || data.message || "Failed to exit car");
//     }
//   } catch (error) {
//     toast.error("Failed to exit car");
//     console.error(error);
//   }
// };
const handleCarExit = async (carNumber: string) => {
  try {
    const response = await fetch(`${apiBaseUrl}/exit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ car_number: carNumber }),
    });

    const data = await response.json();

    if (response.ok) {
      let charge: string | null = null;

      // ✅ Handle structured JSON or string-based message
      if (data.charge !== undefined) {
        charge = data.charge.toString();
      } else if (typeof data.message === "string") {
        const match = data.message.match(/Charge: ₹?([\d.]+)/i);
        if (match) charge = match[1];
      }

      if (charge) {
        toast.success(`🚗 Car ${carNumber} exited. Charge: ₹${charge}`);
      } else {
        toast.success(data.message || `Car ${carNumber} exited successfully`);
      }

      // Optional animation
      const currentSlot = Array.from(occupiedSlots).find(slot => true);
      if (currentSlot) {
        setAnimatingCar({
          carNumber,
          path: [currentSlot, 0],
          isExiting: true,
        });

        setTimeout(() => {
          setAnimatingCar(null);
          fetchVisualization();
        }, 2000);
      } else {
        fetchVisualization();
      }
    } else {
      toast.error(data.detail || data.message || "Failed to exit car");
    }
  } catch (error) {
    toast.error("Failed to exit car");
    console.error(error);
  }
};

 
 
const handleCheckStatus = async (carNumber: string) => {
  try {
    const response = await fetch(`${apiBaseUrl}/status/${encodeURIComponent(carNumber)}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    const data = await response.json();

    if (response.ok) {
      if (data.status === "Parked") {
        toast.info(
          `🚗 Car ${carNumber} is parked in ${data.slot}. (Since ${new Date(
            data.entry_time
          ).toLocaleTimeString()})`
        );
      } else if (data.status === "Queued") {
        toast.info(`⏳ Car ${carNumber} is waiting in queue`);
      } else {
        toast.error(`Car ${carNumber} not found in parking`);
      }
    } else {
      toast.error(data.detail || data.message || "Failed to check status");
    }
  } catch (error) {
    toast.error("Failed to check status");
    console.error(error);
  }
};

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="bg-card border-b border-border py-6 shadow-sm">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl md:text-4xl font-bold text-center text-primary">
            ParkEase – Smart Parking System
          </h1>
          <p className="text-center text-muted-foreground mt-2">DSA-Based Simulation</p>
        </div>
      </header>

      {/* API Base URL Config */}
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center gap-2 max-w-md">
          <label className="text-sm font-medium text-foreground whitespace-nowrap">
            API URL:
          </label>
          <input
            type="text"
            value={apiBaseUrl}
            onChange={(e) => setApiBaseUrl(e.target.value)}
            className="flex-1 px-3 py-1.5 text-sm border border-input rounded-md bg-background"
            placeholder="http://127.0.0.1:8000"
          />
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
          {/* Left Panel - Forms */}
          <div className="lg:col-span-1 space-y-4">
            <AddCarForm onSubmit={handleCarEntry} />
            <ExitCarForm onSubmit={handleCarExit} />
            <StatusCheck onSubmit={handleCheckStatus} />
          </div>

          {/* Right Panel - Parking Grid */}
          <div className="lg:col-span-3 relative">
            <ParkingGrid 
              occupiedSlots={occupiedSlots}
              animatingCar={animatingCar}
            />
            <StatsOverlay stats={stats} />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
