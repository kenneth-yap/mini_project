import math
import random
import heapq
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

class VehicleRoutingSystem:
    """Vehicle routing system that loads network data and calculates optimal paths"""
    
    def __init__(self, map_file_path: str = "map.txt", vehicles_file_path: str = "vehicles.txt"):
        self.nodes = {}
        self.connections = defaultdict(list)
        self.edge_weights = {}
        self.vehicles = {}
        self.map_file_path = map_file_path
        self.vehicles_file_path = vehicles_file_path
        # Track current locations of vehicles (updated by Digital Twin)
        self.vehicle_current_locations = {}
        # Track target locations of vehicles (set by test_dt script)
        self.vehicle_target_locations = {}
        
        # Load data from files
        self._load_network_from_file()
        self._load_vehicles_from_file()
        
    def update_vehicle_location(self, vehicle_id: int, current_node: str):
        """Update the current location of a vehicle (called by Digital Twin data)
        
        After startup, this becomes the authoritative location source
        """
        if vehicle_id not in self.vehicles:
            print(f"Warning: Attempting to update location for unknown vehicle {vehicle_id}")
            return False
            
        if current_node not in self.nodes:
            print(f"Warning: Attempting to set invalid location '{current_node}' for vehicle {vehicle_id}")
            return False
            
        old_location = self.vehicle_current_locations.get(vehicle_id)
        self.vehicle_current_locations[vehicle_id] = current_node
        
        if old_location:
            print(f"Vehicle {vehicle_id} location updated: {old_location} → {current_node}")
        else:
            print(f"Vehicle {vehicle_id} location first tracked: {current_node}")
            print(f"  From now on, this vehicle's location is tracked by Digital Twin")
        
        return True
        
    def set_vehicle_target(self, vehicle_id: int, target_node: str):
        """Set the target location for a vehicle (called by test_dt script)"""
        if vehicle_id not in self.vehicles:
            print(f"Warning: Attempting to set target for unknown vehicle {vehicle_id}")
            return False
            
        if target_node not in self.nodes:
            print(f"Warning: Attempting to set invalid target '{target_node}' for vehicle {vehicle_id}")
            return False
            
        self.vehicle_target_locations[vehicle_id] = target_node
        print(f"Vehicle {vehicle_id} target set to: {target_node}")
        return True
        
    def get_vehicle_current_location(self, vehicle_id: int) -> str:
        """Get the current location of a vehicle
        
        AT STARTUP: Returns start_node from vehicles.txt if never tracked
        AFTER STARTUP: Returns actual tracked location from Digital Twin
        """
        if vehicle_id not in self.vehicles:
            print(f"ERROR: Vehicle {vehicle_id} not found in system")
            return None
            
        # Check if we have a tracked location (updated by Digital Twin)
        current_loc = self.vehicle_current_locations.get(vehicle_id)
        if current_loc:
            # Vehicle location is being actively tracked
            return current_loc
        else:
            # Vehicle location not yet tracked - this should only happen at startup
            # Return the start node from vehicles.txt
            start_loc = self.vehicles[vehicle_id].get('start_node')
            if not start_loc:
                print(f"CRITICAL ERROR: No start location defined for vehicle {vehicle_id} in vehicles.txt")
                return None
            print(f"Vehicle {vehicle_id} using initial location from vehicles.txt: {start_loc}")
            print(f"  (This should only happen at startup before Digital Twin sends first update)")
            return start_loc
            
    def get_vehicle_target_location(self, vehicle_id: int) -> str:
        """Get the target location of a vehicle"""
        return self.vehicle_target_locations.get(vehicle_id, None)
        
    def _load_network_from_file(self):
        """Load network data from map.txt file"""
        try:
            with open(self.map_file_path, 'r') as file:
                print(f"Loading network from: {self.map_file_path}")
                for line in file:
                    line = line.strip()
                    if line:
                        # Parse the format: {{"Node1", {250,50}},["Node2","Node3","Node4","Node5","Node6"]}.
                        print(f"Parsing line: {line}")
                        
                        # Remove outer braces and period
                        line = line.strip('{}.}')
                        
                        # Find the node name (between first two quotes)
                        node_start = line.find('"') + 1
                        node_end = line.find('"', node_start)
                        node_name = line[node_start:node_end]
                        
                        # Find coordinates (between { and })
                        coord_start = line.find('{', node_end) + 1
                        coord_end = line.find('}', coord_start)
                        coords_str = line[coord_start:coord_end]
                        
                        # Parse coordinates
                        coords = coords_str.split(',')
                        x = int(coords[0].strip())
                        y = int(coords[1].strip())
                        
                        self.nodes[node_name] = (x, y)
                        
                        # Find connections (between [ and ])
                        bracket_start = line.find('[')
                        if bracket_start != -1:
                            bracket_end = line.find(']', bracket_start)
                            if bracket_end != -1:
                                connections_str = line[bracket_start+1:bracket_end]
                                if connections_str.strip():
                                    # Split by comma and clean up quotes
                                    connections = [conn.strip().strip('"') for conn in connections_str.split('","')]
                                    # Handle first and last items that might have extra quotes
                                    connections = [conn.strip('"') for conn in connections]
                                    for conn in connections:
                                        if conn:  # Make sure connection is not empty
                                            self.connections[node_name].append(conn)
                        
                        print(f"  Added node: {node_name} at {(x, y)} with connections: {self.connections[node_name]}")
                                        
            print(f"Loaded {len(self.nodes)} nodes from map file")
            self._build_edge_weights()
            
        except FileNotFoundError:
            print(f"Map file not found at {self.map_file_path}")
            raise FileNotFoundError(f"Cannot find map file: {self.map_file_path}")
        except Exception as e:
            print(f"Error parsing map file: {e}")
            raise Exception(f"Error loading map file: {e}")
            
    def _build_edge_weights(self):
        """Calculate distances and assign random weights for all edges"""
        random.seed(42)  # For reproducible results
        
        for node, connected_nodes in self.connections.items():
            for connected_node in connected_nodes:
                if connected_node in self.nodes:
                    # Calculate distance
                    x1, y1 = self.nodes[node]
                    x2, y2 = self.nodes[connected_node]
                    distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                    
                    # Assign weights based on distance
                    carbon_emission = random.uniform(0.1, 2.0) * distance
                    cost = random.uniform(0.5, 3.0) * distance
                    
                    # Store edge weights (use sorted tuple as key for bidirectional edges)
                    edge_key = tuple(sorted([node, connected_node]))
                    if edge_key not in self.edge_weights:
                        self.edge_weights[edge_key] = {
                            'distance': distance,
                            'carbon': carbon_emission,
                            'cost': cost
                        }
    
    def _load_vehicles_from_file(self):
        """Load vehicle data from vehicles.txt file"""
        try:
            with open(self.vehicles_file_path, 'r') as file:
                print(f"Loading vehicles from: {self.vehicles_file_path}")
                for line in file:
                    line = line.strip()
                    if line:
                        # Parse format: {1, 30, "Node1"}.
                        print(f"Parsing vehicle line: {line}")
                        
                        # Remove outer braces and period
                        line = line.strip('{}.')
                        
                        # Split by comma
                        parts = [p.strip() for p in line.split(',')]
                        
                        vehicle_id = int(parts[0])
                        speed = int(parts[1])
                        start_node = parts[2].strip('"')  # Remove quotes
                        
                        self.vehicles[vehicle_id] = {
                            'speed': speed,
                            'start_node': start_node
                        }
                        
                        print(f"  Added vehicle: {vehicle_id}, speed: {speed}, start: {start_node}")
                        
            print(f"Loaded {len(self.vehicles)} vehicles from file")
            
        except FileNotFoundError:
            print(f"Vehicles file not found at {self.vehicles_file_path}")
            raise FileNotFoundError(f"Cannot find vehicles file: {self.vehicles_file_path}")
        except Exception as e:
            print(f"Error parsing vehicles file: {e}")
            raise Exception(f"Error loading vehicles file: {e}")
    
    def get_edge_weight(self, node1: str, node2: str, weight_type: str) -> float:
        """Get edge weight between two nodes"""
        edge_key = tuple(sorted([node1, node2]))
        if edge_key in self.edge_weights:
            return self.edge_weights[edge_key][weight_type]
        return float('inf')
    
    def get_all_neighbors(self, node: str) -> List[str]:
        """Get all neighbors of a node (bidirectional connections)"""
        neighbors = list(self.connections[node])
        
        # Add reverse connections
        for other_node, connections in self.connections.items():
            if node in connections and other_node not in neighbors:
                neighbors.append(other_node)
                
        return neighbors
    
    def dijkstra_shortest_path(self, start_node: str, end_node: str, weight_type: str = 'distance') -> Tuple[List[str], float]:
        """Find shortest path using Dijkstra's algorithm"""
        if start_node not in self.nodes or end_node not in self.nodes:
            return [], float('inf')
        
        # Initialize distances and previous nodes
        distances = {node: float('inf') for node in self.nodes.keys()}
        previous = {node: None for node in self.nodes.keys()}
        distances[start_node] = 0
        
        # Priority queue: (distance, node)
        pq = [(0, start_node)]
        visited = set()
        
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            
            if current_node in visited:
                continue
                
            visited.add(current_node)
            
            if current_node == end_node:
                break
            
            # Check all neighbors (bidirectional)
            neighbors = self.get_all_neighbors(current_node)
            for neighbor in neighbors:
                if neighbor not in visited and neighbor in self.nodes:
                    weight = self.get_edge_weight(current_node, neighbor, weight_type)
                    distance = current_distance + weight
                    
                    if distance < distances[neighbor]:
                        distances[neighbor] = distance
                        previous[neighbor] = current_node
                        heapq.heappush(pq, (distance, neighbor))
        
        # Reconstruct path
        if distances[end_node] == float('inf'):
            return [], float('inf')
        
        path = []
        current = end_node
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        
        return path, distances[end_node]
    
    def calculate_path_metrics(self, path: List[str]) -> Dict[str, float]:
        """Calculate all metrics for a given path"""
        if len(path) < 2:
            return {'distance': 0, 'carbon': 0, 'cost': 0}
        
        total_distance = 0
        total_carbon = 0
        total_cost = 0
        
        for i in range(len(path) - 1):
            total_distance += self.get_edge_weight(path[i], path[i+1], 'distance')
            total_carbon += self.get_edge_weight(path[i], path[i+1], 'carbon')
            total_cost += self.get_edge_weight(path[i], path[i+1], 'cost')
        
        return {
            'distance': total_distance,
            'carbon': total_carbon,
            'cost': total_cost
        }
    
    def get_all_vehicle_times_for_path(self, path: List[str]) -> Dict[int, Dict[str, float]]:
        """Calculate travel time for a path for ALL vehicles in the system"""
        if len(path) < 2:
            return {}
        
        vehicle_times = {}
        path_metrics = self.calculate_path_metrics(path)
        
        print(f"Calculating travel times for path: {' → '.join(path)}")
        print(f"Path distance: {path_metrics['distance']:.2f} units")
        
        for vehicle_id, vehicle_data in self.vehicles.items():
            speed = vehicle_data['speed']
            travel_time = path_metrics['distance'] / speed if speed > 0 else float('inf')
            
            vehicle_times[vehicle_id] = {
                'travel_time': travel_time,
                'speed': speed,
                'distance': path_metrics['distance'],
                'carbon': path_metrics['carbon'],
                'cost': path_metrics['cost']
            }
            
            print(f"  Vehicle {vehicle_id}: Speed={speed}, Time={travel_time:.2f}")
        
        return vehicle_times
        """Calculate travel time for a path using specific vehicle speed"""
        if len(path) < 2:
            return 0
            
        if vehicle_id not in self.vehicles:
            print(f"Warning: Vehicle {vehicle_id} not found in vehicles data. Available vehicles: {list(self.vehicles.keys())}")
            return float('inf')
        
        vehicle_speed = self.vehicles[vehicle_id]['speed']
        path_metrics = self.calculate_path_metrics(path)
        total_distance = path_metrics['distance']
        
        if vehicle_speed <= 0:
            print(f"Warning: Vehicle {vehicle_id} has invalid speed: {vehicle_speed}")
            return float('inf')
            
        travel_time = total_distance / vehicle_speed
        print(f"Vehicle {vehicle_id} (speed: {vehicle_speed}) - Distance: {total_distance:.2f}, Time: {travel_time:.2f}")
        
    def calculate_travel_time(self, path: List[str], vehicle_id: int) -> float:
        """Calculate travel time for a path using specific vehicle speed"""
        if len(path) < 2:
            return 0
            
        if vehicle_id not in self.vehicles:
            print(f"Warning: Vehicle {vehicle_id} not found in vehicles data. Available vehicles: {list(self.vehicles.keys())}")
            return float('inf')
        
        vehicle_speed = self.vehicles[vehicle_id]['speed']
        path_metrics = self.calculate_path_metrics(path)
        total_distance = path_metrics['distance']
        
        if vehicle_speed <= 0:
            print(f"Warning: Vehicle {vehicle_id} has invalid speed: {vehicle_speed}")
            return float('inf')
            
        travel_time = total_distance / vehicle_speed
        # Removed verbose logging - only one vehicle per agent
        
        return travel_time
        
    def get_all_vehicle_times_for_route(self, start_node: str, end_node: str, priority: int = 1) -> Dict[str, Dict]:
        """Calculate optimal paths and times for ALL vehicles for a specific route"""
        results = {}
        
        # Get all possible optimal paths (distance, carbon, cost only - time is derived)
        priority_map = {1: 'distance', 2: 'carbon', 3: 'cost'}
        
        for priority_num, criterion_name in priority_map.items():
            # Get optimal path for this criterion
            path, _ = self.dijkstra_shortest_path(start_node, end_node, criterion_name)
            
            if not path:
                continue
                
            path_metrics = self.calculate_path_metrics(path)
            vehicle_times = {}
            
            # Calculate times for all vehicles on this path
            for vehicle_id, vehicle_data in self.vehicles.items():
                speed = vehicle_data['speed']
                travel_time = path_metrics['distance'] / speed if speed > 0 else float('inf')
                
                vehicle_times[vehicle_id] = {
                    'travel_time': travel_time,
                    'speed': speed,
                    'start_node': vehicle_data['start_node']
                }
            
            results[criterion_name] = {
                'path': path,
                'distance': path_metrics['distance'],
                'carbon': path_metrics['carbon'],
                'cost': path_metrics['cost'],
                'vehicle_times': vehicle_times,
                'criterion': f"Optimized for {criterion_name.title()}"
            }
        
        return results
    
    def find_all_optimal_paths(self, start_node: str, end_node: str, vehicle_id: int) -> Dict[str, Dict]:
        """Find optimal paths for all criteria and return with metrics"""
        # Validate inputs
        if start_node not in self.nodes:
            print(f"Error: Start node '{start_node}' not found in network. Available nodes: {list(self.nodes.keys())}")
            return {}
            
        if end_node not in self.nodes:
            print(f"Error: End node '{end_node}' not found in network. Available nodes: {list(self.nodes.keys())}")
            return {}
            
        if vehicle_id not in self.vehicles:
            print(f"Error: Vehicle {vehicle_id} not found. Available vehicles: {list(self.vehicles.keys())}")
            return {}
            
        print(f"Finding optimal paths from {start_node} to {end_node} for Vehicle {vehicle_id}")
        print(f"Vehicle {vehicle_id} speed: {self.vehicles[vehicle_id]['speed']} units/time")
        
        results = {}
        
        # 1. Shortest Distance Path
        distance_path, distance_value = self.dijkstra_shortest_path(start_node, end_node, 'distance')
        if distance_path:
            distance_metrics = self.calculate_path_metrics(distance_path)
            travel_time = self.calculate_travel_time(distance_path, vehicle_id)
            
            results['distance'] = {
                'path': distance_path,
                'distance': distance_metrics['distance'],
                'carbon': distance_metrics['carbon'],
                'cost': distance_metrics['cost'],
                'travel_time': travel_time,
                'criterion': 'Shortest Distance'
            }
        
        # 2. Lowest Carbon Emission Path
        carbon_path, carbon_value = self.dijkstra_shortest_path(start_node, end_node, 'carbon')
        if carbon_path:
            carbon_metrics = self.calculate_path_metrics(carbon_path)
            travel_time = self.calculate_travel_time(carbon_path, vehicle_id)
            
            results['carbon'] = {
                'path': carbon_path,
                'distance': carbon_metrics['distance'],
                'carbon': carbon_metrics['carbon'],
                'cost': carbon_metrics['cost'],
                'travel_time': travel_time,
                'criterion': 'Lowest Carbon Emission'
            }
        
        # 3. Lowest Cost Path
        cost_path, cost_value = self.dijkstra_shortest_path(start_node, end_node, 'cost')
        if cost_path:
            cost_metrics = self.calculate_path_metrics(cost_path)
            travel_time = self.calculate_travel_time(cost_path, vehicle_id)
            
            results['cost'] = {
                'path': cost_path,
                'distance': cost_metrics['distance'],
                'carbon': cost_metrics['carbon'],
                'cost': cost_metrics['cost'],
                'travel_time': travel_time,
                'criterion': 'Lowest Cost'
            }
        
        # 4. Find fastest travel time (try all paths and pick fastest)
        fastest_time = float('inf')
        fastest_path = []
        
        for criterion in ['distance', 'carbon', 'cost']:
            temp_path, _ = self.dijkstra_shortest_path(start_node, end_node, criterion)
            if temp_path:
                temp_time = self.calculate_travel_time(temp_path, vehicle_id)
                if temp_time < fastest_time:
                    fastest_time = temp_time
                    fastest_path = temp_path
        
        if fastest_path:
            time_metrics = self.calculate_path_metrics(fastest_path)
            results['time'] = {
                'path': fastest_path,
                'distance': time_metrics['distance'],
                'carbon': time_metrics['carbon'],
                'cost': time_metrics['cost'],
                'travel_time': fastest_time,
                'criterion': 'Fastest Travel Time'
            }
        
        return results
    
    def find_optimal_path_for_vehicle(self, vehicle_id: int, destination: str, priority: int = 1, override_start: str = None) -> Optional[Dict]:
        """Find optimal path for a specific vehicle using their current location - NO DANGEROUS DEFAULTS"""
        
        # Validate vehicle exists
        if vehicle_id not in self.vehicles:
            print(f"CRITICAL ERROR: Vehicle {vehicle_id} not found. Available vehicles: {list(self.vehicles.keys())}")
            return None
            
        # Get current location (either override or tracked location)
        if override_start:
            start_node = override_start
            print(f"Using override start location for Vehicle {vehicle_id}: {start_node}")
        else:
            start_node = self.get_vehicle_current_location(vehicle_id)
            
        if not start_node:
            print(f"CRITICAL ERROR: Cannot determine starting location for Vehicle {vehicle_id}")
            return None
        
        # Validate start node exists in network
        if start_node not in self.nodes:
            print(f"CRITICAL ERROR: Start node '{start_node}' not found in network for Vehicle {vehicle_id}")
            return None
            
        # Validate destination
        if destination not in self.nodes:
            print(f"CRITICAL ERROR: Destination '{destination}' not found in network. Available nodes: {list(self.nodes.keys())}")
            return None
            
        # Set target for tracking
        self.set_vehicle_target(vehicle_id, destination)
        
        # Reduced logging - only show key info
        print(f"Route: Vehicle {vehicle_id} ({start_node} → {destination})")
        
        # Get optimal path based on priority
        optimal_path_data = self.get_optimal_path_by_priority(start_node, destination, vehicle_id, priority)
        
        if optimal_path_data:
            print(f"Path found: {' → '.join(optimal_path_data['path'])} (Time: {optimal_path_data['travel_time']:.2f})")
        else:
            print(f"CRITICAL ERROR: No path found for Vehicle {vehicle_id} from {start_node} to {destination}")
        
        return optimal_path_data
    def get_optimal_path_by_priority(self, start_node: str, end_node: str, vehicle_id: int, priority: int) -> Optional[Dict]:
        """Get optimal path based on priority (1=distance, 2=carbon, 3=cost, 4=time)"""
        # Validate that we have the correct vehicle
        if vehicle_id not in self.vehicles:
            print(f"Error: Vehicle {vehicle_id} not found in vehicles data!")
            return None
            
        # Route calculation with vehicle-specific data
        print(f"Route calculation: Vehicle {vehicle_id} from {start_node} to {end_node} (Priority: {priority})")
        print(f"Vehicle {vehicle_id} data: Speed={self.vehicles[vehicle_id]['speed']}, "
              f"Start node from file={self.vehicles[vehicle_id]['start_node']}")
        
        all_paths = self.find_all_optimal_paths(start_node, end_node, vehicle_id)
        
        if not all_paths:
            print(f"No paths found from {start_node} to {end_node} for Vehicle {vehicle_id}")
            return None
        
        priority_map = {
            1: 'distance',
            2: 'carbon', 
            3: 'cost',
            4: 'time'
        }
        
        criterion = priority_map.get(priority, 'distance')
        selected_path = all_paths.get(criterion)
        
        if selected_path:
            print(f"Selected path ({criterion}) for Vehicle {vehicle_id}: {' → '.join(selected_path['path'])}")
            print(f"Using Vehicle {vehicle_id} speed: {self.vehicles[vehicle_id]['speed']} for time calculation")
            print(f"Travel time for Vehicle {vehicle_id}: {selected_path['travel_time']:.2f} time units")
        else:
            print(f"No {criterion} path found for Vehicle {vehicle_id}")
        
        return selected_path
        
    def get_vehicle_status(self, vehicle_id: int) -> Dict:
        """Get comprehensive status of a specific vehicle"""
        if vehicle_id not in self.vehicles:
            return {"error": f"Vehicle {vehicle_id} not found"}
            
        vehicle_data = self.vehicles[vehicle_id].copy()
        current_location = self.get_vehicle_current_location(vehicle_id)
        target_location = self.get_vehicle_target_location(vehicle_id)
        
        return {
            "vehicle_id": vehicle_id,
            "speed": vehicle_data['speed'],
            "start_node_from_file": vehicle_data['start_node'],
            "current_location": current_location,
            "target_location": target_location,
            "location_tracked": vehicle_id in self.vehicle_current_locations
        }
    
    def print_all_vehicle_analysis(self, start_node: str, end_node: str):
        """Print comprehensive analysis showing how each vehicle would perform on each optimal path"""
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE VEHICLE ANALYSIS: {start_node} → {end_node}")
        print(f"{'='*80}")
        
        # Get all optimal paths
        all_routes = self.get_all_vehicle_times_for_route(start_node, end_node)
        
        if not all_routes:
            print("No routes found!")
            return
        
        # Print summary table header
        print(f"\n{'Path Type':<20} {'Path':<30} {'Distance':<12} {'Carbon':<12} {'Cost':<12}")
        print("-" * 86)
        
        for criterion, route_data in all_routes.items():
            path_str = ' → '.join(route_data['path'][:4]) + ('...' if len(route_data['path']) > 4 else '')
            print(f"{criterion.title():<20} {path_str:<30} {route_data['distance']:<12.1f} "
                  f"{route_data['carbon']:<12.1f} {route_data['cost']:<12.1f}")
        
        # Print detailed vehicle times for each path
        for criterion, route_data in all_routes.items():
            print(f"\n{criterion.upper()} PATH: {' → '.join(route_data['path'])}")
            print(f"Path Metrics - Distance: {route_data['distance']:.2f}, "
                  f"Carbon: {route_data['carbon']:.2f}, Cost: {route_data['cost']:.2f}")
            print("Vehicle Travel Times:")
            
            # Sort vehicles by travel time for this path
            sorted_vehicles = sorted(route_data['vehicle_times'].items(), 
                                   key=lambda x: x[1]['travel_time'])
            
            for vehicle_id, vehicle_data in sorted_vehicles:
                print(f"  Vehicle {vehicle_id}: {vehicle_data['travel_time']:.2f} time units "
                      f"(speed: {vehicle_data['speed']})")
        
        # Find fastest vehicle for each path type
        print(f"\n{'='*60}")
        print("FASTEST VEHICLE FOR EACH PATH TYPE:")
        print("="*60)
        
        for criterion, route_data in all_routes.items():
            fastest_vehicle = min(route_data['vehicle_times'].items(), 
                                key=lambda x: x[1]['travel_time'])
            vehicle_id, vehicle_data = fastest_vehicle
            print(f"{criterion.title():<20}: Vehicle {vehicle_id} "
                  f"({vehicle_data['travel_time']:.2f} time units, speed: {vehicle_data['speed']})")

    def print_path_summary(self, start_node: str, end_node: str, vehicle_id: int):
        """Print summary of all optimal paths for a specific vehicle"""
        print(f"\n{'='*60}")
        print(f"ROUTE ANALYSIS: {start_node} → {end_node} (Vehicle {vehicle_id})")
        print(f"{'='*60}")
        
        if vehicle_id in self.vehicles:
            speed = self.vehicles[vehicle_id]['speed']
            start_location = self.vehicles[vehicle_id]['start_node']
            print(f"Vehicle {vehicle_id} - Speed: {speed} units/time, Original start: {start_location}")
        
        all_paths = self.find_all_optimal_paths(start_node, end_node, vehicle_id)
        
        for criterion_key, data in all_paths.items():
            print(f"\n{data['criterion'].upper()}:")
            print(f"  Path: {' → '.join(data['path'])}")
            print(f"  Distance: {data['distance']:.2f} units")
            print(f"  Carbon: {data['carbon']:.2f} kg CO2")
            print(f"  Cost: ${data['cost']:.2f}")
            print(f"  Travel Time: {data['travel_time']:.2f} time units")

# Example usage and testing
def main():
    # File paths - modify as needed
    map_file = "map.txt"
    vehicles_file = "vehicles.txt"
    
    try:
        # Initialize routing system
        routing_system = VehicleRoutingSystem(map_file, vehicles_file)
        
        print("\n" + "="*50)
        print("VEHICLE ROUTING SYSTEM INITIALIZED")
        print("="*50)
        print(f"Nodes loaded: {len(routing_system.nodes)}")
        print(f"Vehicles loaded: {len(routing_system.vehicles)}")
        
        # Example route analysis
        start_node = "Node1"
        end_node = "Node12"
        vehicle_id = 1
        
        # Test the new vehicle-specific functionality
        print(f"\n{'='*60}")
        print("TESTING VEHICLE-SPECIFIC ROUTING")
        print("="*60)
        
        # Test with vehicle tracking
        test_vehicle_id = 1
        
        # Simulate Digital Twin updating vehicle location
        routing_system.update_vehicle_location(test_vehicle_id, "Node2")
        
        # Test route planning with tracked location
        destination = "Node12"
        print(f"\nTesting route for Vehicle {test_vehicle_id} to {destination}")
        
        # Show vehicle status
        status = routing_system.get_vehicle_status(test_vehicle_id)
        print(f"Vehicle {test_vehicle_id} status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Test routing with current location
        optimal_route = routing_system.find_optimal_path_for_vehicle(test_vehicle_id, destination, priority=1)
        if optimal_route:
            print(f"\nOptimal route for Vehicle {test_vehicle_id}:")
            print(f"  Path: {' → '.join(optimal_route['path'])}")
            print(f"  Travel time: {optimal_route['travel_time']:.2f} time units")
        
        # Test with override start location
        override_start = "Node5"
        print(f"\nTesting with override start location: {override_start}")
        override_route = routing_system.find_optimal_path_for_vehicle(
            test_vehicle_id, destination, priority=1, override_start=override_start)
        if override_route:
            print(f"Route with override start:")
            print(f"  Path: {' → '.join(override_route['path'])}")
            print(f"  Travel time: {override_route['travel_time']:.2f} time units")
        
        # Example route analysis with comprehensive vehicle comparison
        start_node = "Node1"
        end_node = "Node12"
        vehicle_id = 1
        
        # Print detailed analysis for specific vehicle
        routing_system.print_path_summary(start_node, end_node, vehicle_id)
        
        # Print comprehensive analysis for ALL vehicles
        routing_system.print_all_vehicle_analysis(start_node, end_node)
        
        # Test each priority for the specific vehicle
        print(f"\n{'='*60}")
        print("PRIORITY-BASED PATH SELECTION")
        print("="*60)
        
        priorities = {
            1: "Shortest Distance",
            2: "Lowest Carbon Emission", 
            3: "Lowest Cost",
            4: "Fastest Travel Time"
        }
        
        for priority, name in priorities.items():
            optimal_path = routing_system.get_optimal_path_by_priority(start_node, end_node, vehicle_id, priority)
            if optimal_path:
                print(f"\nPriority {priority} ({name}) for Vehicle {vehicle_id}:")
                print(f"  Selected Path: {' → '.join(optimal_path['path'])}")
                print(f"  Metrics: D={optimal_path['distance']:.1f}, C={optimal_path['carbon']:.1f}, "
                      f"Cost={optimal_path['cost']:.1f}, Time={optimal_path['travel_time']:.2f}")
        
        # Test the comprehensive vehicle analysis functionality
        print(f"\n{'='*60}")
        print("TESTING ALL-VEHICLE ROUTE ANALYSIS")
        print("="*60)
        
        all_vehicle_routes = routing_system.get_all_vehicle_times_for_route(start_node, end_node)
        for criterion, route_data in all_vehicle_routes.items():
            print(f"\n{criterion.upper()} path:")
            fastest_vehicle_id = min(route_data['vehicle_times'].items(), 
                                   key=lambda x: x[1]['travel_time'])[0]
            fastest_time = route_data['vehicle_times'][fastest_vehicle_id]['travel_time']
            print(f"  Best vehicle: {fastest_vehicle_id} (Time: {fastest_time:.2f})")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure map.txt and vehicles.txt files exist in the current directory")

if __name__ == "__main__":
    main()