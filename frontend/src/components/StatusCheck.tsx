import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Search } from "lucide-react";

interface StatusCheckProps {
  onSubmit: (carNumber: string) => void;
}

export const StatusCheck = ({ onSubmit }: StatusCheckProps) => {
  const [carNumber, setCarNumber] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (carNumber.trim()) {
      onSubmit(carNumber.trim());
    }
  };

  return (
    <Card className="border-accent/20 shadow-md">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg flex items-center gap-2">
          <Search className="h-5 w-5 text-accent" />
          Status Check
        </CardTitle>
        <CardDescription>Check vehicle status</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="status-car-number">Car Number</Label>
            <Input
              id="status-car-number"
              type="text"
              placeholder="e.g., ABC123"
              value={carNumber}
              onChange={(e) => setCarNumber(e.target.value)}
              required
            />
          </div>
          <Button type="submit" variant="secondary" className="w-full">
            Check Status
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
