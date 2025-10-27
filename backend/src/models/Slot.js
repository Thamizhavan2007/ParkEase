import mongoose from "mongoose";

const slotSchema = new mongoose.Schema({
  slotNumber: { type: Number, required: true, unique: true },
  occupied: { type: Boolean, default: false },
  vehicle: { type: mongoose.Schema.Types.ObjectId, ref: "Vehicle", default: null }
});

const Slot = mongoose.model("Slot", slotSchema);
export default Slot;
