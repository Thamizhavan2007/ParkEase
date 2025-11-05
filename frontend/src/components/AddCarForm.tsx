import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PlusCircle } from "lucide-react";

interface AddCarFormProps {
  onSubmit: (carNumber: string) => void;
}

export const AddCarForm = ({ onSubmit }: AddCarFormProps) => {
  const [carNumber, setCarNumber] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (carNumber.trim()) {
      onSubmit(carNumber.trim());
      setCarNumber("");
    }
  };

  return (
    <Card className="border-primary/20 shadow-md">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg flex items-center gap-2">
          <PlusCircle className="h-5 w-5 text-primary" />
          Add Car
        </CardTitle>
        <CardDescription>Enter a new vehicle</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="add-car-number">Car Number</Label>
            <Input
              id="add-car-number"
              type="text"
              placeholder="e.g., ABC123"
              value={carNumber}
              onChange={(e) => setCarNumber(e.target.value)}
              required
            />
          </div>
          <Button type="submit" className="w-full">
            Add Car
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
