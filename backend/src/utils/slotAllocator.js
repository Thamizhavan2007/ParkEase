import Slot from "../models/Slot.js";

/**
 * Graph representation of the parking layout
 * Nodes: 0 (entry), 1-20 slots
 * Edges: adjacent slots with distance 1
 */
const graph = {
  0: { 1: 1, 6: 1 }, // entry connects to nearest slots
  1: { 2: 1, 6: 1 },
  2: { 1: 1, 3: 1, 7: 1 },
  3: { 2: 1, 4: 1, 8: 1 },
  4: { 3: 1, 5: 1, 9: 1 },
  5: { 4: 1, 10: 1 },
  6: { 0: 1, 1: 1, 7: 1, 11: 1 },
  7: { 2: 1, 6: 1, 8: 1, 12: 1 },
  8: { 3: 1, 7: 1, 9: 1, 13: 1 },
  9: { 4: 1, 8: 1, 10: 1, 14: 1 },
  10: { 5: 1, 9: 1, 15: 1 },
  11: { 6: 1, 12: 1, 16: 1 },
  12: { 7: 1, 11: 1, 13: 1, 17: 1 },
  13: { 8: 1, 12: 1, 14: 1, 18: 1 },
  14: { 9: 1, 13: 1, 15: 1, 19: 1 },
  15: { 10: 1, 14: 1, 20: 1 },
  16: { 11: 1, 17: 1 },
  17: { 12: 1, 16: 1, 18: 1 },
  18: { 13: 1, 17: 1, 19: 1 },
  19: { 14: 1, 18: 1, 20: 1 },
  20: { 15: 1, 19: 1 }
};

/**
 * Dijkstra algorithm
 */
const dijkstra = (graph, start) => {
  const distances = {};
  const visited = new Set();
  const prev = {};

  // Initialize distances
  Object.keys(graph).forEach(node => distances[node] = Infinity);
  distances[start] = 0;

  while (visited.size < Object.keys(graph).length) {
    // Pick unvisited node with smallest distance
    let currentNode = null;
    let minDistance = Infinity;
    for (let node in distances) {
      if (!visited.has(node) && distances[node] < minDistance) {
        minDistance = distances[node];
        currentNode = node;
      }
    }
    if (currentNode === null) break;

    visited.add(currentNode);

    // Update neighbors
    for (let neighbor in graph[currentNode]) {
      const alt = distances[currentNode] + graph[currentNode][neighbor];
      if (alt < distances[neighbor]) {
        distances[neighbor] = alt;
        prev[neighbor] = currentNode;
      }
    }
  }

  return distances;
};

/**
 * Get nearest free slot based on Dijkstra distances from entry
 */
export const getNearestFreeSlot = async () => {
  const freeSlots = await Slot.find({ occupied: false });

  if (!freeSlots.length) return null;

  const distances = dijkstra(graph, "0");

  // Find free slot with minimum distance from entry
  let nearestSlot = freeSlots[0];
  let minDist = distances[nearestSlot.slotNumber];

  for (let slot of freeSlots) {
    if (distances[slot.slotNumber] < minDist) {
      nearestSlot = slot;
      minDist = distances[slot.slotNumber];
    }
  }

  return nearestSlot;
};
