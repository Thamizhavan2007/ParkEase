import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LogOut } from "lucide-react";

interface ExitCarFormProps {
  onSubmit: (carNumber: string) => void;
}

export const ExitCarForm = ({ onSubmit }: ExitCarFormProps) => {
  const [carNumber, setCarNumber] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (carNumber.trim()) {
      onSubmit(carNumber.trim());
      setCarNumber("");
    }
  };

  return (
    <Card className="border-destructive/20 shadow-md">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg flex items-center gap-2">
          <LogOut className="h-5 w-5 text-destructive" />
          Exit Car
        </CardTitle>
        <CardDescription>Remove a vehicle</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="exit-car-number">Car Number</Label>
            <Input
              id="exit-car-number"
              type="text"
              placeholder="e.g., ABC123"
              value={carNumber}
              onChange={(e) => setCarNumber(e.target.value)}
              required
            />
          </div>
          <Button type="submit" variant="destructive" className="w-full">
            Exit Car
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
